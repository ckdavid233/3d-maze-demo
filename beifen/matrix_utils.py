import numpy as np

def get_model_matrix(angle=0):
    rad = np.radians(angle)
    cos_a, sin_a = np.cos(rad), np.sin(rad)
    model = np.array([
        [cos_a, 0, sin_a, 0],
        [0, 1, 0, 0],
        [-sin_a, 0, cos_a, 0],
        [0, 0, 0, 1],
    ], dtype=np.float32)
    return model


def get_view_matrix(camera_pos, camera_front, camera_up):
    f = camera_front / np.linalg.norm(camera_front)
    r = np.cross(f, camera_up)
    r = r / np.linalg.norm(r)
    u = np.cross(r, f)

    view = np.identity(4, dtype=np.float32)
    view[0, :3] = r
    view[1, :3] = u
    view[2, :3] = -f
    view[:3, 3] = -np.dot(view[:3, :3], camera_pos)
    return view

def get_projection_matrix(fov, aspect, near, far):
    """透视投影矩阵"""
    f = 1 / np.tan(np.radians(fov) / 2)
    proj = np.zeros((4, 4), dtype=np.float32)
    proj[0, 0] = f / aspect
    proj[1, 1] = f
    proj[2, 2] = (far + near) / (near - far)
    proj[2, 3] = (2 * far * near) / (near - far)
    proj[3, 2] = -1
    return proj