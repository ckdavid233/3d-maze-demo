import numpy as np
import math
import time


class Camera:
    def __init__(self, position=np.array([0, 2, 3], dtype=np.float32),
                 up=np.array([0, 1, 0], dtype=np.float32),
                 yaw=-90.0, pitch=0.0,
                 speed=5, sensitivity=0.1):
        self.position = position
        self.world_up = up
        self.yaw = yaw
        self.pitch = pitch
        self.initial_height = self.position[1]

        self.speed = speed
        self.sensitivity = sensitivity

        self.front = np.array([0, 0, -1], dtype=np.float32)
        self.right = None
        self.up = None
        

        self.last_jump_time = -float('inf')  # 初始化为负无穷，表示一开始可以跳
        self.jump_cooldown = 1  # 跳跃冷却时间（秒）

        # 物理相关
        self.velocity_y = 0.0  # Y轴速度（重力）
        self.gravity = -15.0  # 重力加速度
        self.is_grounded = False
        self.player_height = 1.8  # 玩家身高
        self.player_radius = 0.3  # 玩家碰撞半径
        self.jump_strength = 8.0  # 跳跃力度

        # 走路摇晃效果
        self.head_bob_timer = 0.0
        self.head_bob_intensity = 0.15  # 摇晃强度
        self.head_bob_speed = 8.0  # 摇晃频率
        self.is_moving = False

        self.update_camera_vectors()

    def update_camera_vectors(self):
        # 计算摄像机前方向量（单位向量）
        yaw_rad = np.radians(self.yaw)
        pitch_rad = np.radians(self.pitch)

        front = np.array([
            np.cos(yaw_rad) * np.cos(pitch_rad),
            np.sin(pitch_rad),
            np.sin(yaw_rad) * np.cos(pitch_rad)
        ], dtype=np.float32)

        self.front = front / np.linalg.norm(front)
        self.right = np.cross(self.front, self.world_up)
        self.right /= np.linalg.norm(self.right)
        self.up = np.cross(self.right, self.front)
        self.up /= np.linalg.norm(self.up)

    def check_collision(self, new_position, cubes):
        """检查与方块的碰撞"""
        player_min = new_position - np.array([self.player_radius, 0, self.player_radius])
        player_max = new_position + np.array([self.player_radius, self.player_height, self.player_radius])

        for cube_pos in cubes:
            # 每个方块大小为2x2x2，中心在cube_pos
            cube_min = cube_pos - np.array([1, 1, 1])
            cube_max = cube_pos + np.array([1, 1, 1])

            # AABB碰撞检测
            if (player_min[0] < cube_max[0] and player_max[0] > cube_min[0] and
                    player_min[1] < cube_max[1] and player_max[1] > cube_min[1] and
                    player_min[2] < cube_max[2] and player_max[2] > cube_min[2]):
                return True
        return False

    def check_ground_collision(self, cubes):
        """检查脚下是否有地面（方块顶部）"""
        foot_y = self.position[1] - 0.1 # 脚的位置

        for cube_pos in cubes:
            cube_min = cube_pos - np.array([1, 1, 1])
            cube_max = cube_pos + np.array([1, 1, 1])

            # 检查玩家是否在方块的X,Z范围内
            if (self.position[0] - self.player_radius < cube_max[0] and
                    self.position[0] + self.player_radius > cube_min[0] and
                    self.position[2] - self.player_radius < cube_max[2] and
                    self.position[2] + self.player_radius > cube_min[2]):

                # 检查是否站在方块顶部
                if foot_y <= cube_max[1] and foot_y >= cube_max[1] - 0.5:
                    return cube_max[1]

        # 检查是否在地面（Y=0）- 地面方块在Y=-1，所以顶部是Y=0
        if foot_y <= 0.1:
            return 0.0

        return None

    def jump(self):
        """跳跃功能：每次跳跃后需等待 cooldown 时间"""
        current_time = time.time()
        if current_time - self.last_jump_time >= self.jump_cooldown:
            self.velocity_y = self.jump_strength
            self.last_jump_time = current_time


    def process_keyboard(self, direction, delta_time, cubes):
        velocity = self.speed * delta_time
        old_position = self.position.copy()

        # 只在XZ平面移动（水平移动）
        movement = np.array([0, 0, 0], dtype=np.float32)

        if direction == "FORWARD":
            # 只使用front的XZ分量
            front_xz = np.array([self.front[0], 0, self.front[2]], dtype=np.float32)
            front_xz = front_xz / np.linalg.norm(front_xz) if np.linalg.norm(front_xz) > 0 else front_xz
            movement += front_xz * velocity
        elif direction == "BACKWARD":
            front_xz = np.array([self.front[0], 0, self.front[2]], dtype=np.float32)
            front_xz = front_xz / np.linalg.norm(front_xz) if np.linalg.norm(front_xz) > 0 else front_xz
            movement -= front_xz * velocity
        elif direction == "LEFT":
            movement -= self.right * velocity
        elif direction == "RIGHT":
            movement += self.right * velocity

        # 检查X轴碰撞
        test_pos = old_position + np.array([movement[0], 0, 0])
        if not self.check_collision(test_pos, cubes):
            self.position[0] = test_pos[0]

        # 检查y轴碰撞
        test_pos = old_position + np.array([0, movement[1], 0])
        if not self.check_collision(test_pos, cubes):
            self.position[1] = test_pos[1]

        # 检查Z轴碰撞
        test_pos = old_position + np.array([0, 0, movement[2]])
        if not self.check_collision(test_pos, cubes):
            self.position[2] = test_pos[2]

    def update_physics(self, delta_time, cubes):
        """更新物理（重力和地面检测）"""
        # 检查地面
        ground_y = self.check_ground_collision(cubes)

        if ground_y is not None:
            # 在地面上
            if self.position[1] <= ground_y + 0.01:
                self.position[1] = ground_y
                self.velocity_y = 0
                self.is_grounded = True
            else:
                self.is_grounded = False
        else:
            self.is_grounded = False

        # 应用重力
        if not self.is_grounded:
            self.velocity_y += self.gravity * delta_time
            new_y = self.position[1] + self.velocity_y * delta_time

            # 检查Y轴碰撞
            test_pos = self.position.copy()
            test_pos[1] = new_y
            if not self.check_collision(test_pos, cubes):
                self.position[1] = new_y

    def update_head_bob(self, delta_time):
        """更新头部摇晃效果 - 修复：只有在移动且在地面时才摇晃"""
        if self.is_moving and self.is_grounded:
            self.head_bob_timer += delta_time * self.head_bob_speed
        else:
            # 平滑回到中心位置 - 更快的衰减
            self.head_bob_timer *= 0.8  # 更快停止摇晃

    def process_mouse_movement(self, xoffset, yoffset, constrain_pitch=True):
        xoffset *= self.sensitivity
        yoffset *= self.sensitivity

        self.yaw += xoffset
        self.pitch += yoffset
        self.yaw = self.yaw % 360

        if constrain_pitch:
            self.pitch = max(min(self.pitch, 89.0), -89.0)

        self.update_camera_vectors()

    def get_view_matrix(self):
        """获取视图矩阵，包含头部摇晃效果"""
        # 基础摄像机位置
        camera_pos = self.position.copy()

        # 添加头部摇晃效果 - 只有在实际移动时才有效果
        if self.is_moving and self.is_grounded and abs(self.head_bob_timer) > 0.01:
            bob_offset_y = math.sin(self.head_bob_timer) * self.head_bob_intensity
            bob_offset_x = math.cos(self.head_bob_timer * 0.5) * self.head_bob_intensity * 0.5

            camera_pos[1] += bob_offset_y
            camera_pos += self.right * bob_offset_x

        # 计算视图矩阵
        center = camera_pos + self.front

        f = (center - camera_pos)
        f /= np.linalg.norm(f)

        r = np.cross(f, self.up)
        r /= np.linalg.norm(r)

        u = np.cross(r, f)

        view = np.eye(4, dtype=np.float32)

        view[0, :3] = r
        view[1, :3] = u
        view[2, :3] = -f

        view[:3, 3] = -view[:3, :3] @ camera_pos

        return view