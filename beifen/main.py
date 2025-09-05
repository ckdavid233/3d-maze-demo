import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

import numpy as np
from cube_data import vertices, indices
from matrix_utils import get_projection_matrix
from camera import Camera

# 初始化窗口
pygame.init()
width, height = 800, 600
pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL)
pygame.display.set_caption("3D 第一人称场景")

# OpenGL 设置
glEnable(GL_DEPTH_TEST)
glClearColor(0.1, 0.1, 0.1, 1.0)

# 投影矩阵
fov = 120
aspect_ratio = width / height
projection = get_projection_matrix(fov, aspect_ratio, 0.1, 100.0)

# 摄像机
camera = Camera(position=np.array([0, 1.5, 5], dtype=np.float32))
clock = pygame.time.Clock()

# 鼠标设置
pygame.mouse.set_visible(False)
pygame.event.set_grab(True)
last_x, last_y = width // 2, height // 2
first_mouse = True

# 按键状态
key_state = {
    "W": False,
    "S": False,
    "A": False,
    "D": False
}

# ---- 绘图函数 ----
def draw_cube(offset=np.array([0, 0, 0])):
    glColor3f(1.0, 1.0, 1.0)
    glBegin(GL_LINES)
    for edge in indices:
        for vertex in edge:
            v = vertices[vertex][:3] + offset
            glVertex3fv(v)
    glEnd()

def draw_grid(size=20, step=1):
    glColor3f(0.3, 0.3, 0.3)
    glBegin(GL_LINES)
    for i in range(-size, size + 1, step):
        glVertex3f(i, 0, -size)
        glVertex3f(i, 0, size)
        glVertex3f(-size, 0, i)
        glVertex3f(size, 0, i)
    glEnd()

# ---- 主循环 ----
running = True
while running:
    delta_time = clock.tick(60) / 1000.0

    # 事件处理
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False
        elif event.type == KEYDOWN:
            # 按键处理
            if event.key == pygame.K_ESCAPE:
                running = False
            if event.key == pygame.K_w:
                key_state["W"] = True
            if event.key == pygame.K_s:
                key_state["S"] = True
            if event.key == pygame.K_a:
                key_state["A"] = True
            if event.key == pygame.K_d:
                key_state["D"] = True
        elif event.type == KEYUP:
            if event.key == pygame.K_w:
                key_state["W"] = False
            if event.key == pygame.K_s:
                key_state["S"] = False
            if event.key == pygame.K_a:
                key_state["A"] = False
            if event.key == pygame.K_d:
                key_state["D"] = False

    # **新增：获取鼠标相对移动**
    x_offset, y_offset = pygame.mouse.get_rel()
    camera.process_mouse_movement(x_offset, -y_offset)  # 注意y轴通常反转
    # 键盘移动
    if key_state["W"]:
        camera.process_keyboard("FORWARD", delta_time)
    if key_state["S"]:
        camera.process_keyboard("BACKWARD", delta_time)
    if key_state["A"]:
        camera.process_keyboard("LEFT", delta_time)
    if key_state["D"]:
        camera.process_keyboard("RIGHT", delta_time)

    # 清屏
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # 视图矩阵设置
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    mvp = projection @ camera.get_view_matrix()
    glMultMatrixf(mvp.T)

    # 绘制内容
    draw_grid()
    cube_positions = [
        np.array([0, 0.5, 0]),
        np.array([3, 0.5, 0]),
        np.array([-3, 0.5, -3]),
        np.array([0, 0.5, -5]),
        np.array([-2, 0.5, 2]),
    ]
    for pos in cube_positions:
        draw_cube(pos)

    pygame.display.flip()

pygame.quit()
