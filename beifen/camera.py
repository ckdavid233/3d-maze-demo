import numpy as np

class Camera:
    def __init__(self, position=np.array([0, 0, 3], dtype=np.float32),
                 up=np.array([0, 1, 0], dtype=np.float32),
                 yaw=-90.0, pitch=0.0,
                 speed=5, sensitivity=0.1):
        self.position = position
        self.world_up = up
        self.yaw = yaw
        self.pitch = pitch

        self.speed = speed
        self.sensitivity = sensitivity

        self.front = np.array([0, 0, -1], dtype=np.float32)

        self.right = None
        self.up = None

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
        # 右方向 = 前方向叉乘世界上方向
        self.right = np.cross(self.front, self.world_up)
        self.right /= np.linalg.norm(self.right)
        # 真实的上方向 = 右叉乘前
        self.up = np.cross(self.right, self.front)
        self.up /= np.linalg.norm(self.up)

    def process_keyboard(self, direction, delta_time):
        velocity = self.speed * delta_time
        if direction == "FORWARD":
            self.position += self.front * velocity
        elif direction == "BACKWARD":
            self.position -= self.front * velocity
        elif direction == "LEFT":
            self.position -= self.right * velocity
        elif direction == "RIGHT":
            self.position += self.right * velocity

    def process_mouse_movement(self, xoffset, yoffset, constrain_pitch=True):
        xoffset *= self.sensitivity
        yoffset *= self.sensitivity

        self.yaw += xoffset
        self.pitch += yoffset
        self.yaw = self.yaw % 360
        # 限制pitch防止上下看头歪
        if constrain_pitch:
            self.pitch = max(min(self.pitch, 89.0), -89.0)

        self.update_camera_vectors()

    def get_view_matrix(self):
        # 实现 LookAt 矩阵
        center = self.position + self.front

        f = (center - self.position)
        f /= np.linalg.norm(f)

        r = np.cross(f, self.up)
        r /= np.linalg.norm(r)

        u = np.cross(r, f)

        view = np.eye(4, dtype=np.float32)

        view[0, :3] = r
        view[1, :3] = u
        view[2, :3] = -f

        view[:3, 3] = -view[:3, :3] @ self.position

        return view
