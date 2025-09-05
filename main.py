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
pygame.display.set_caption("3D 第一人称场景 - 重力碰撞版")

# OpenGL 设置
glEnable(GL_DEPTH_TEST)
glClearColor(0.1, 0.1, 0.1, 1.0)

# 投影矩阵
fov = 90  # 减小FOV让视野更自然
aspect_ratio = width / height
projection = get_projection_matrix(fov, aspect_ratio, 0.1, 100.0)

# 摄像机 - 修正出生位置，确保在地面上方正确高度
camera = Camera(position=np.array([2, 2, 2], dtype=np.float32))  # 调整为合适的出生位置和高度
clock = pygame.time.Clock()

# 鼠标设置
pygame.mouse.set_visible(False)
pygame.event.set_grab(True)

# 按键状态
key_state = {
    "W": False,
    "S": False,
    "A": False,
    "D": False,
    "SPACE": False
}


# 创建8x8的迷宫 - 减少内存占用
def create_maze():
    maze_positions = []

    # 迷宫设计 - 8x8的网格，使用1和0表示墙和路
    # 1 = 墙壁, 0 = 通路
    maze_layout = [
        [1, 1, 1, 1, 1, 1, 1, 1],
        [1, 0, 1, 0, 0, 0, 0, 1],
        [1, 0, 1, 0, 1, 1, 0, 1],
        [1, 0, 0, 0, 0, 1, 0, 1],
        [1, 1, 1, 1, 0, 1, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 1, 1, 1, 1, 0, 1],
        [1, 1, 1, 1, 1, 1, 1, 1],
    ]

    # 地面 - 填充整个区域，每个方块紧贴放置
    for x in range(8):
        for z in range(8):
            maze_positions.append(np.array([x * 2, -1, z * 2], dtype=np.float32))  # 间距改为2

    # 根据迷宫布局创建墙壁 - 墙壁下移到地面上
    for z in range(8):
        for x in range(8):
            if maze_layout[z][x] == 1:  # 如果是墙
                # 墙壁从地面开始，高度为2个单位，墙壁现在在 y=1 和 y=3（原来是y=1和y=3，现在改为y=0和y=2）
                maze_positions.append(np.array([x * 2, 0, z * 2], dtype=np.float32))  # 下移1个单位
                maze_positions.append(np.array([x * 2, 2, z * 2], dtype=np.float32))  # 下移1个单位

    return maze_positions


cube_positions = create_maze()


# ---- 绘图函数 ----
def draw_filled_cube(offset=np.array([0, 0, 0]), color=(1.0, 1.0, 1.0)):
    """绘制填充的立方体"""
    # 立方体的6个面
    faces = [
        # 前面
        [0, 1, 3, 2],
        # 后面
        [4, 6, 7, 5],
        # 左面
        [0, 2, 6, 4],
        # 右面
        [1, 5, 7, 3],
        # 上面
        [2, 3, 7, 6],
        # 下面
        [0, 4, 5, 1]
    ]

    glColor3f(*color)

    # 绘制填充的面
    for face in faces:
        glBegin(GL_QUADS)
        for vertex_index in face:
            v = vertices[vertex_index][:3] + offset
            glVertex3fv(v)
        glEnd()

    # 绘制更清晰的边框线条
    glLineWidth(2.0)  # 增加线条宽度
    glColor3f(0.0, 0.0, 0.0)  # 黑色边框
    glBegin(GL_LINES)
    for edge in indices:
        for vertex in edge:
            v = vertices[vertex][:3] + offset
            glVertex3fv(v)
    glEnd()
    glLineWidth(1.0)  # 恢复默认线条宽度


def draw_ground_cube(offset=np.array([0, 0, 0]), color=(1.0, 1.0, 1.0)):
    """只绘制地面方块的底面，上移一个格子"""
    # 只绘制底面 [0, 4, 5, 1]，但上移一个格子
    glColor3f(*color)
    glBegin(GL_QUADS)
    for vertex_index in [0, 4, 5, 1]:  # 底面的顶点索引
        v = vertices[vertex_index][:3] + offset
        v[1] += 1  # 上移一个格子（每个格子高度为2）
        glVertex3fv(v)
    glEnd()


def draw_cube_wireframe(offset=np.array([0, 0, 0]), color=(1.0, 1.0, 1.0)):
    """绘制线框立方体（用于地面）"""
    glLineWidth(2.0)  # 增加线条宽度
    glColor3f(*color)
    glBegin(GL_LINES)
    for edge in indices:
        for vertex in edge:
            v = vertices[vertex][:3] + offset
            glVertex3fv(v)
    glEnd()
    glLineWidth(1.0)  # 恢复默认线条宽度


def draw_grid(size=20, step=2):  # 调整网格以匹配新的方块间距
    glColor3f(0.2, 0.2, 0.2)
    glBegin(GL_LINES)
    for i in range(-size, size + 1, step):
        glVertex3f(i, 0, -size)
        glVertex3f(i, 0, size)
        glVertex3f(-size, 0, i)
        glVertex3f(size, 0, i)
    glEnd()


def draw_crosshair():
    """绘制准星"""
    # 保存当前矩阵
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, width, 0, height, -1, 1)

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    # 禁用深度测试以确保准星在最前面
    glDisable(GL_DEPTH_TEST)

    glColor3f(1.0, 1.0, 1.0)
    glLineWidth(2.0)  # 增加准星线条宽度
    glBegin(GL_LINES)
    # 水平线
    glVertex2f(width / 2 - 10, height / 2)
    glVertex2f(width / 2 + 10, height / 2)
    # 垂直线
    glVertex2f(width / 2, height / 2 - 10)
    glVertex2f(width / 2, height / 2 + 10)
    glEnd()
    glLineWidth(1.0)  # 恢复默认线条宽度

    # 恢复深度测试
    glEnable(GL_DEPTH_TEST)

    # 恢复矩阵
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


# ---- 主循环 ----
running = True
while running:
    delta_time = clock.tick(60) / 1000.0

    # 事件处理
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False
        elif event.type == KEYDOWN:
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
            if event.key == pygame.K_SPACE:
                camera.jump()  # ✅ 直接调用跳跃，只触发一次
        elif event.type == KEYUP:
            if event.key == pygame.K_w:
                key_state["W"] = False
            if event.key == pygame.K_s:
                key_state["S"] = False
            if event.key == pygame.K_a:
                key_state["A"] = False
            if event.key == pygame.K_d:
                key_state["D"] = False


    # 鼠标移动
    x_offset, y_offset = pygame.mouse.get_rel()
    camera.process_mouse_movement(x_offset, -y_offset)

    # 键盘移动（现在包含碰撞检测）
    any_key_pressed = False
    if key_state["W"]:
        camera.process_keyboard("FORWARD", delta_time, cube_positions)
        any_key_pressed = True
    if key_state["S"]:
        camera.process_keyboard("BACKWARD", delta_time, cube_positions)
        any_key_pressed = True
    if key_state["A"]:
        camera.process_keyboard("LEFT", delta_time, cube_positions)
        any_key_pressed = True
    if key_state["D"]:
        camera.process_keyboard("RIGHT", delta_time, cube_positions)
        any_key_pressed = True
    if key_state["SPACE"]:
        camera.jump()  # 添加跳跃功能

    # 更新移动状态 - 只有在按键时才设为True
    camera.is_moving = any_key_pressed

    # 更新物理（重力）和头部摇晃
    camera.update_physics(delta_time, cube_positions)
    camera.update_head_bob(delta_time)

    # 清屏
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # 视图矩阵设置
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    mvp = projection @ camera.get_view_matrix()
    glMultMatrixf(mvp.T)

    # 绘制内容
    # draw_grid()  # 注释掉网格线，地面不要有线条

    # 绘制所有方块
    for i, pos in enumerate(cube_positions):
        if pos[1] <= -1:  # 地面方块 - 只渲染底面
            color = (0.4, 0.3, 0.2)  # 棕色地面
            draw_ground_cube(pos, color)
        else:  # 墙壁方块 - 用填充
            # 入口区域标记
            if pos[0] == 2 and pos[2] == 2:  # 调整入口位置
                color = (0.2, 0.8, 0.2)  # 亮绿色 - 入口
            # 出口区域标记 - 调整为8x8迷宫的出口位置
            elif pos[0] == 12 and pos[2] == 12:  # 调整出口位置(6*2=12)
                color = (0.8, 0.2, 0.2)  # 红色 - 出口
            else:
                color = (0.6, 0.6, 0.8)  # 蓝灰色 - 普通墙壁
            draw_filled_cube(pos, color)

    # 绘制准星
    draw_crosshair()

    pygame.display.flip()

pygame.quit()