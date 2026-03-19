import taichi as ti
import math

# 初始化Taichi，CPU/GPU都能运行
ti.init(arch=ti.cpu)

# 定义立方体的8个顶点（中心在原点，边长2）
vertices = ti.Vector.field(3, dtype=ti.f32, shape=8)
# 存储顶点投影后的屏幕坐标
screen_coords = ti.Vector.field(2, dtype=ti.f32, shape=8)
# 定义立方体的12条边（每两个顶点组成一条边）
edges = [
    (0, 1), (1, 2), (2, 3), (3, 0),  # 顶面
    (4, 5), (5, 6), (6, 7), (7, 4),  # 底面
    (0, 4), (1, 5), (2, 6), (3, 7)   # 竖边
]
# 定义立方体的6个面（每个面由4个顶点组成，用于填充）
faces = [
    (0, 1, 2, 3),  # 顶面
    (4, 5, 6, 7),  # 底面
    (0, 1, 5, 4),  # 前面
    (1, 2, 6, 5),  # 右面
    (2, 3, 7, 6),  # 后面
    (3, 0, 4, 7)   # 左面
]

@ti.func
def get_model_matrix(angle: ti.f32):
    """模型矩阵：绕Y轴旋转"""
    rad = angle * math.pi / 180.0
    c = ti.cos(rad)
    s = ti.sin(rad)
    return ti.Matrix([
        [c,  0.0, s, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [-s, 0.0, c, 0.0],
        [0.0, 0.0, 0.0, 1.0]
    ])

@ti.func
def get_view_matrix(eye_pos):
    """视图矩阵：相机位置"""
    return ti.Matrix([
        [1.0, 0.0, 0.0, -eye_pos[0]],
        [0.0, 1.0, 0.0, -eye_pos[1]],
        [0.0, 0.0, 1.0, -eye_pos[2]],
        [0.0, 0.0, 0.0, 1.0]
    ])

@ti.func
def get_projection_matrix(eye_fov: ti.f32, aspect_ratio: ti.f32, zNear: ti.f32, zFar: ti.f32):
    """投影矩阵：透视投影转正交投影"""
    n = -zNear
    f = -zFar
    fov_rad = eye_fov * math.pi / 180.0
    t = ti.tan(fov_rad / 2.0) * ti.abs(n)
    b = -t
    r = aspect_ratio * t
    l = -r

    # 透视转正交
    M_p2o = ti.Matrix([
        [n, 0.0, 0.0, 0.0],
        [0.0, n, 0.0, 0.0],
        [0.0, 0.0, n + f, -n * f],
        [0.0, 0.0, 1.0, 0.0]
    ])

    # 正交投影缩放和平移
    M_ortho_scale = ti.Matrix([
        [2.0 / (r - l), 0.0, 0.0, 0.0],
        [0.0, 2.0 / (t - b), 0.0, 0.0],
        [0.0, 0.0, 2.0 / (n - f), 0.0],
        [0.0, 0.0, 0.0, 1.0]
    ])

    M_ortho_trans = ti.Matrix([
        [1.0, 0.0, 0.0, -(r + l) / 2.0],
        [0.0, 1.0, 0.0, -(t + b) / 2.0],
        [0.0, 0.0, 1.0, -(n + f) / 2.0],
        [0.0, 0.0, 0.0, 1.0]
    ])

    M_ortho = M_ortho_scale @ M_ortho_trans
    return M_ortho @ M_p2o

@ti.kernel
def compute_transform(angle: ti.f32):
    """计算MVP矩阵，将3D顶点投影到2D屏幕"""
    # 相机位置：z轴正方向，距离原点5个单位
    eye_pos = ti.Vector([0.0, 0.0, 5.0])
    # 计算MVP矩阵（投影×视图×模型）
    model = get_model_matrix(angle)
    view = get_view_matrix(eye_pos)
    proj = get_projection_matrix(45.0, 1.0, 0.1, 50.0)
    mvp = proj @ view @ model

    # 对每个顶点进行变换
    for i in range(8):
        v = vertices[i]
        v4 = ti.Vector([v[0], v[1], v[2], 1.0])  # 转齐次坐标
        v_clip = mvp @ v4                       # MVP变换
        v_ndc = v_clip / v_clip[3]              # 透视除法
        # 转换为屏幕坐标（NDC[-1,1] → 屏幕[0,1]）
        screen_coords[i][0] = (v_ndc[0] + 1.0) / 2.0
        screen_coords[i][1] = (v_ndc[1] + 1.0) / 2.0

def main():
    # 初始化立方体8个顶点坐标（中心在原点，边长2）
    vertices[0] = [1.0, 1.0, 1.0]
    vertices[1] = [-1.0, 1.0, 1.0]
    vertices[2] = [-1.0, 1.0, -1.0]
    vertices[3] = [1.0, 1.0, -1.0]
    vertices[4] = [1.0, -1.0, 1.0]
    vertices[5] = [-1.0, -1.0, 1.0]
    vertices[6] = [-1.0, -1.0, -1.0]
    vertices[7] = [1.0, -1.0, -1.0]

    # 创建GUI窗口，分辨率600×600
    gui = ti.GUI("3D立方体渲染", res=(600, 600), background_color=0x111111)
    angle = 0.0  # 旋转角度

    while gui.running:
        # 1. 旋转控制：自动旋转（也可按A/D手动控制）
        angle += 0.5  # 每次循环旋转0.5度
        if gui.is_pressed(ti.GUI.LEFT, 'a'):
            angle += 1.0
        if gui.is_pressed(ti.GUI.RIGHT, 'd'):
            angle -= 1.0

        # 2. 退出控制
        if gui.get_event(ti.GUI.PRESS):
            if gui.event.key == ti.GUI.ESCAPE:
                break

        # 3. 计算顶点投影坐标
        compute_transform(angle)

        # 4. 绘制立方体：先填充面（白色），再画边框（彩色）
        # 填充6个面（白色）
        for face in faces:
            p1, p2, p3, p4 = screen_coords[face[0]], screen_coords[face[1]], screen_coords[face[2]], screen_coords[face[3]]
            # 绘制两个三角形组成一个面
            gui.triangle(p1, p2, p3, color=0xFFFFFF)
            gui.triangle(p1, p3, p4, color=0xFFFFFF)
        
        # 绘制12条边（彩色边框，半径2）
        edge_colors = [0xFF0000, 0xFF0000, 0xFF0000, 0xFF0000,  # 顶面：红
                       0x00FF00, 0x00FF00, 0x00FF00, 0x00FF00,  # 底面：绿
                       0x0000FF, 0x0000FF, 0x0000FF, 0x0000FF]  # 竖边：蓝
        for i, (v1, v2) in enumerate(edges):
            gui.line(screen_coords[v1], screen_coords[v2], radius=2, color=edge_colors[i])

        # 5. 显示画面
        gui.show()

if __name__ == '__main__':
    main()