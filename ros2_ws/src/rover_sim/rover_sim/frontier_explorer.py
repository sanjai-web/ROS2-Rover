#!/usr/bin/env python3
"""
frontier_explorer.py

ROS2 node implementing frontier-based exploration for the rover.

Algorithm:
  1. Subscribe to /map (OccupancyGrid) and /odom (Odometry)
  2. Find frontier cells: free cells (=0) adjacent to unknown cells (=-1)
  3. Cluster frontiers via BFS into connected groups
  4. Pick the largest cluster closest to the robot
  5. Send NavigateToPose goal to Nav2
  6. On completion, find next frontier — repeat until no frontiers remain
  7. Call map_saver_cli to save the final map

QoS:
  - /map uses TRANSIENT_LOCAL + RELIABLE (required by slam_toolbox)
  - /odom uses best-effort
"""

import math
import subprocess
import sys
from collections import deque

import numpy as np
import rclpy
from action_msgs.msg import GoalStatus
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose
from nav_msgs.msg import OccupancyGrid, Odometry
from rclpy.action import ActionClient
from rclpy.node import Node
from rclpy.qos import (
    DurabilityPolicy,
    HistoryPolicy,
    QoSProfile,
    ReliabilityPolicy,
)
from visualization_msgs.msg import Marker, MarkerArray


class FrontierExplorer(Node):
    """Autonomous frontier-based exploration node."""

    def __init__(self):
        super().__init__('frontier_explorer')

        # ── Parameters ──────────────────────────────────────────────────────────
        self.declare_parameter('min_frontier_size', 5)
        self.declare_parameter('goal_tolerance', 0.3)
        self.declare_parameter('robot_radius', 0.35)
        self.declare_parameter('map_save_path', '/tmp/rover_map')

        self.min_frontier_size = self.get_parameter('min_frontier_size').value
        self.goal_tolerance    = self.get_parameter('goal_tolerance').value
        self.robot_radius      = self.get_parameter('robot_radius').value
        self.map_save_path     = self.get_parameter('map_save_path').value

        # ── State ────────────────────────────────────────────────────────────────
        self.map_data: OccupancyGrid | None = None
        self.robot_x: float = 0.0
        self.robot_y: float = 0.0
        self.navigating: bool = False
        self.exploration_done: bool = False

        # ── QoS profiles ─────────────────────────────────────────────────────────
        map_qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
        )
        sensor_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=5,
        )

        # ── Subscribers ───────────────────────────────────────────────────────────
        self.map_sub = self.create_subscription(
            OccupancyGrid, '/map', self._map_callback, map_qos)
        self.odom_sub = self.create_subscription(
            Odometry, '/odom', self._odom_callback, sensor_qos)

        # ── Nav2 Action client ────────────────────────────────────────────────────
        self._nav_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')

        # ── Visualization publisher ───────────────────────────────────────────────
        self.marker_pub = self.create_publisher(
            MarkerArray, '/frontier_markers', 10)

        # ── Timer: check for frontiers every 2 s ─────────────────────────────────
        self._explore_timer = self.create_timer(2.0, self._explore_tick)

        self.get_logger().info('FrontierExplorer started — waiting for map and nav2 ...')

    # ── Callbacks ────────────────────────────────────────────────────────────────

    def _map_callback(self, msg: OccupancyGrid):
        self.map_data = msg

    def _odom_callback(self, msg: Odometry):
        self.robot_x = msg.pose.pose.position.x
        self.robot_y = msg.pose.pose.position.y

    # ── Core exploration tick ─────────────────────────────────────────────────────

    def _explore_tick(self):
        if self.exploration_done or self.navigating:
            return
        if self.map_data is None:
            self.get_logger().info('Waiting for /map ...', throttle_duration_sec=5.0)
            return

        frontiers = self._find_frontiers()
        if not frontiers:
            self.get_logger().info('No frontiers found — exploration complete!')
            self.exploration_done = True
            self._explore_timer.cancel()
            self._save_map()
            return

        self.get_logger().info(f'Found {len(frontiers)} frontier clusters')
        self._publish_frontier_markers(frontiers)

        # Select best frontier: largest cluster closest to robot
        goal_x, goal_y = self._select_goal(frontiers)
        self._send_nav_goal(goal_x, goal_y)

    # ── Frontier detection ─────────────────────────────────────────────────────────

    def _find_frontiers(self) -> list[tuple[float, float, int]]:
        """
        Returns list of (centroid_x, centroid_y, cluster_size) for each
        valid frontier cluster.
        """
        msg = self.map_data
        width  = msg.info.width
        height = msg.info.height
        res    = msg.info.resolution
        ox     = msg.info.origin.position.x
        oy     = msg.info.origin.position.y

        grid = np.array(msg.data, dtype=np.int8).reshape((height, width))

        # Frontier cells: free (0) with at least one unknown (-1) neighbour
        free    = (grid == 0)
        unknown = (grid == -1)

        # 4-connected neighbour check for unknown
        has_unknown_neighbour = np.zeros_like(free, dtype=bool)
        has_unknown_neighbour[:-1, :] |= unknown[1:, :]   # up
        has_unknown_neighbour[1:,  :] |= unknown[:-1, :]  # down
        has_unknown_neighbour[:, :-1] |= unknown[:, 1:]   # right
        has_unknown_neighbour[:, 1:]  |= unknown[:, :-1]  # left

        frontier_mask = free & has_unknown_neighbour
        frontier_indices = list(zip(*np.where(frontier_mask)))

        if not frontier_indices:
            return []

        # BFS cluster frontier cells
        visited = np.zeros_like(frontier_mask, dtype=bool)
        clusters: list[tuple[float, float, int]] = []

        for r, c in frontier_indices:
            if visited[r, c]:
                continue
            # BFS
            cluster_cells = [(r, c)]
            queue = deque([(r, c)])
            visited[r, c] = True
            while queue:
                cr, cc = queue.popleft()
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = cr + dr, cc + dc
                    if (0 <= nr < height and 0 <= nc < width
                            and not visited[nr, nc]
                            and frontier_mask[nr, nc]):
                        visited[nr, nc] = True
                        cluster_cells.append((nr, nc))
                        queue.append((nr, nc))

            if len(cluster_cells) < self.min_frontier_size:
                continue

            # Centroid in world coordinates
            avg_r = sum(rr for rr, _ in cluster_cells) / len(cluster_cells)
            avg_c = sum(cc for _, cc in cluster_cells) / len(cluster_cells)
            wx = ox + (avg_c + 0.5) * res
            wy = oy + (avg_r + 0.5) * res
            clusters.append((wx, wy, len(cluster_cells)))

        return clusters

    # ── Goal selection ─────────────────────────────────────────────────────────────

    def _select_goal(self, frontiers: list) -> tuple[float, float]:
        """
        Score = cluster_size / (distance_to_robot + 1)
        Pick maximum score.
        """
        best_score = -1.0
        best_x, best_y = 0.0, 0.0
        for (fx, fy, sz) in frontiers:
            dist = math.hypot(fx - self.robot_x, fy - self.robot_y)
            score = sz / (dist + 1.0)
            if score > best_score:
                best_score = score
                best_x, best_y = fx, fy
        return best_x, best_y

    # ── Navigation ──────────────────────────────────────────────────────────────────

    def _send_nav_goal(self, x: float, y: float):
        self.get_logger().info(f'Sending goal → ({x:.2f}, {y:.2f})')

        if not self._nav_client.wait_for_server(timeout_sec=5.0):
            self.get_logger().warn('NavigateToPose server not available')
            return

        goal_msg = NavigateToPose.Goal()
        goal_msg.pose.header.frame_id = 'map'
        goal_msg.pose.header.stamp    = self.get_clock().now().to_msg()
        goal_msg.pose.pose.position.x = x
        goal_msg.pose.pose.position.y = y
        goal_msg.pose.pose.orientation.w = 1.0

        self.navigating = True
        send_future = self._nav_client.send_goal_async(
            goal_msg,
            feedback_callback=self._feedback_callback,
        )
        send_future.add_done_callback(self._goal_response_callback)

    def _goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().warn('Goal rejected by Nav2')
            self.navigating = False
            return
        self.get_logger().info('Goal accepted by Nav2')
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self._goal_result_callback)

    def _goal_result_callback(self, future):
        result = future.result()
        status = result.status
        self.navigating = False
        if status == GoalStatus.STATUS_SUCCEEDED:
            self.get_logger().info('Goal reached — searching for next frontier')
        elif status == GoalStatus.STATUS_CANCELED:
            self.get_logger().warn('Goal cancelled')
        else:
            self.get_logger().warn(f'Goal failed with status: {status}')

    def _feedback_callback(self, feedback_msg):
        # Could log distance to goal here if desired
        pass

    # ── Map saving ─────────────────────────────────────────────────────────────────

    def _save_map(self):
        self.get_logger().info(f'Saving map to {self.map_save_path} ...')
        try:
            subprocess.run(
                ['ros2', 'run', 'nav2_map_server', 'map_saver_cli',
                 '-f', self.map_save_path,
                 '--ros-args', '-p', 'use_sim_time:=true'],
                check=True, timeout=30,
            )
            self.get_logger().info(f'Map saved: {self.map_save_path}.pgm / .yaml')
        except Exception as e:
            self.get_logger().error(f'Failed to save map: {e}')

    # ── Visualization ───────────────────────────────────────────────────────────────

    def _publish_frontier_markers(self, frontiers: list):
        ma = MarkerArray()
        for i, (fx, fy, sz) in enumerate(frontiers):
            m = Marker()
            m.header.frame_id = 'map'
            m.header.stamp    = self.get_clock().now().to_msg()
            m.ns = 'frontiers'
            m.id = i
            m.type = Marker.CYLINDER
            m.action = Marker.ADD
            m.pose.position.x = fx
            m.pose.position.y = fy
            m.pose.position.z = 0.25
            m.pose.orientation.w = 1.0
            m.scale.x = 0.3
            m.scale.y = 0.3
            m.scale.z = 0.5
            m.color.r = 0.0
            m.color.g = 1.0
            m.color.b = 0.5
            m.color.a = 0.8
            m.lifetime.sec = 3
            ma.markers.append(m)
        self.marker_pub.publish(ma)


def main(args=None):
    rclpy.init(args=args)
    node = FrontierExplorer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
