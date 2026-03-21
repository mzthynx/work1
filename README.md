### 一、实验目标 🎯
深入理解 3D 空间中模型 - 视图 - 投影（MVP）变换的完整流程，掌握坐标变换的数学原理。  
独立推导并实现模型变换（Model）、视图变换（View）和投影变换（Projection）三个核心 4×4 齐次坐标矩阵。  
掌握面向数据编程框架 Taichi 的基本语法与矩阵操作，完成从 3D 顶点到 2D 屏幕坐标的映射与绘制。  
（选做）将基础任务中的三角形升级为三维立方体，实现透视旋转效果，直观感受 3D 空间感。

### <font style="color:rgb(0, 0, 0);background-color:rgba(0, 0, 0, 0);">二、实验原理与核心概念 </font><font style="color:rgb(0, 0, 0);background-color:rgba(0, 0, 0, 0);">📚</font>
#### <font style="color:rgb(0, 0, 0);background-color:rgba(0, 0, 0, 0);">2.1 MVP 变换流程</font>
<font style="color:rgb(0, 0, 0);background-color:rgba(0, 0, 0, 0);">从 3D 世界坐标到 2D 屏幕坐标的变换分为三个阶段：</font>

<font style="color:rgb(0, 0, 0);background-color:rgba(0, 0, 0, 0);">模型变换（Model）</font><font style="color:rgb(0, 0, 0);background-color:rgba(0, 0, 0, 0);">：将物体从局部坐标系变换到世界坐标系，本实验中主要实现绕 Z 轴（或 Y/X 轴）的旋转变换。</font>

<font style="color:rgb(0, 0, 0);background-color:rgba(0, 0, 0, 0);">视图变换（View）</font><font style="color:rgb(0, 0, 0);background-color:rgba(0, 0, 0, 0);">：将相机位置平移至世界坐标系原点，模拟 “相机看向物体” 的视角。</font>

<font style="color:rgb(0, 0, 0);background-color:rgba(0, 0, 0, 0);">投影变换（Projection）</font><font style="color:rgb(0, 0, 0);background-color:rgba(0, 0, 0, 0);">：将 3D 坐标投影到 2D 平面，本实验采用</font><font style="color:rgb(0, 0, 0);background-color:rgba(0, 0, 0, 0);">透视投影</font><font style="color:rgb(0, 0, 0);background-color:rgba(0, 0, 0, 0);">，实现近大远小的视觉效果。</font>

<font style="color:rgb(0, 0, 0);background-color:rgba(0, 0, 0, 0);">视口变换</font><font style="color:rgb(0, 0, 0);background-color:rgba(0, 0, 0, 0);">：将归一化设备坐标（NDC）映射到屏幕像素坐标。</font>

#### <font style="color:rgb(0, 0, 0);background-color:rgba(0, 0, 0, 0);">2.2 核心矩阵推导</font>
<font style="color:rgb(0, 0, 0);background-color:rgba(0, 0, 0, 0);">（1）模型变换矩阵（绕 Z 轴旋转）</font>

<font style="color:rgb(0, 0, 0);background-color:rgba(0, 0, 0, 0);">绕 Z 轴旋转</font>$ \theta $<font style="color:rgb(0, 0, 0);background-color:rgba(0, 0, 0, 0);">角（角度制）的模型矩阵为：</font>

$$
M_{\text{model}} = 
\begin{bmatrix}
\cos\theta & -\sin\theta & 0 & 0 \\
\sin\theta & \cos\theta & 0 & 0 \\
0 & 0 & 1 & 0 \\
0 & 0 & 0 & 1
\end{bmatrix}
$$

<font style="color:rgb(0, 0, 0);background-color:rgba(0, 0, 0, 0);">其中</font>$ \theta $<font style="color:rgb(0, 0, 0);background-color:rgba(0, 0, 0, 0);">需先转换为弧度：</font>$ \theta _{rad}=\theta *\pi /180 $

<font style="color:rgb(0, 0, 0);background-color:rgba(0, 0, 0, 0);">（2）视图变换矩阵</font>

<font style="color:rgb(0, 0, 0);background-color:rgba(0, 0, 0, 0);">将相机从位置</font>`<font style="color:rgb(0, 0, 0);background-color:rgba(0, 0, 0, 0);">eye_pos</font>`<font style="color:rgb(0, 0, 0);background-color:rgba(0, 0, 0, 0);">平移至原点的视图矩阵为：</font>

$$
M_{\text{view}} = 
\begin{bmatrix}
1 & 0 & 0 & -\mathrm{eye\_pos}.x \\
0 & 1 & 0 & -\mathrm{eye\_pos}.y \\
0 & 0 & 1 & -\mathrm{eye\_pos}.z \\
0 & 0 & 0 & 1
\end{bmatrix}
$$

<font style="color:rgb(0, 0, 0);background-color:rgba(0, 0, 0, 0);">（3）透视投影矩阵</font>

<font style="color:rgb(0, 0, 0);background-color:rgba(0, 0, 0, 0);">透视投影分为两步：</font>

<font style="color:rgb(0, 0, 0);background-color:rgba(0, 0, 0, 0);">透视→正交变换</font><font style="color:rgb(0, 0, 0);background-color:rgba(0, 0, 0, 0);">：将透视平截头体挤压为正交长方体。</font>

<font style="color:rgb(0, 0, 0);background-color:rgba(0, 0, 0, 0);">正交投影变换</font><font style="color:rgb(0, 0, 0);background-color:rgba(0, 0, 0, 0);">：将长方体映射到 NDC 空间。</font>

<font style="color:rgb(0, 0, 0);background-color:rgba(0, 0, 0, 0);">最终投影矩阵为：</font>

$$
M_{\text{proj}} = M_{\text{ortho}} \times M_{\text{persp}\rightarrow\text{ortho}}
$$

其中：

$$
M_{\text{persp}\rightarrow\text{ortho}} = 
\begin{bmatrix}
n & 0 & 0 & 0 \\
0 & n & 0 & 0 \\
0 & 0 & n+f & -nf \\
0 & 0 & 1 & 0
\end{bmatrix}
$$

$$
M_{\text{ortho}} = 
\begin{bmatrix}
\frac{2}{r-l} & 0 & 0 & -\frac{r+l}{r-l} \\
0 & \frac{2}{t-b} & 0 & -\frac{t+b}{t-b} \\
0 & 0 & \frac{2}{n-f} & -\frac{n+f}{n-f} \\
0 & 0 & 0 & 1
\end{bmatrix}
$$

$$
n = -\mathrm{zNear},\ f = -\mathrm{zFar},\ t = \tan\left(\frac{\mathrm{fov}}{2}\right) \cdot |n|,\ b = -t,\ r = \mathrm{aspect\_ratio} \cdot t
$$

### <font style="color:rgb(0, 0, 0);background-color:rgba(0, 0, 0, 0);">三、实验环境与工具 </font><font style="color:rgb(0, 0, 0);background-color:rgba(0, 0, 0, 0);">🛠️</font>
<font style="color:rgb(0, 0, 0);background-color:rgba(0, 0, 0, 0);">编程语言：Python 3.8+</font>

<font style="color:rgb(0, 0, 0);background-color:rgba(0, 0, 0, 0);">图形框架：Taichi</font>

<font style="color:rgb(0, 0, 0);background-color:rgba(0, 0, 0, 0);">开发工具：TARE</font>

<font style="color:rgb(0, 0, 0);background-color:rgba(0, 0, 0, 0);">版本控制：Git + GitHub</font>

### <font style="color:rgb(0, 0, 0);background-color:rgba(0, 0, 0, 0);">四、实验内容与代码实现 </font><font style="color:rgb(0, 0, 0);background-color:rgba(0, 0, 0, 0);">💻</font>
#### <font style="color:rgb(0, 0, 0);background-color:rgba(0, 0, 0, 0);">4.1 基础任务：三角形线框渲染</font>
4.1.1 核心函数实现

1. get_model_matrix(angle)

```python
@ti.func
def get_model_matrix(angle: ti.f32):
    rad = angle * math.pi / 180.0
    c = ti.cos(rad)
    s = ti.sin(rad)
    return ti.Matrix([
        [c, -s, 0.0, 0.0],
        [s,  c, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0]
    ])
```

2. get_view_matrix(eye_pos)

```python
@ti.func
def get_view_matrix(eye_pos):
    return ti.Matrix([
        [1.0, 0.0, 0.0, -eye_pos[0]],
        [0.0, 1.0, 0.0, -eye_pos[1]],
        [0.0, 0.0, 1.0, -eye_pos[2]],
        [0.0, 0.0, 0.0, 1.0]
    ])
```

3. get_projection_matrix

```python
@ti.func
def get_projection_matrix(eye_fov: ti.f32, aspect_ratio: ti.f32, zNear: ti.f32, zFar: ti.f32):
    n = -zNear
    f = -zFar
    fov_rad = eye_fov * math.pi / 180.0
    t = ti.tan(fov_rad / 2.0) * ti.abs(n)
    b = -t
    r = aspect_ratio * t
    l = -r

    M_p2o = ti.Matrix([
        [n, 0.0, 0.0, 0.0],
        [0.0, n, 0.0, 0.0],
        [0.0, 0.0, n + f, -n * f],
        [0.0, 0.0, 1.0, 0.0]
    ])

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
```

 4.1.2 渲染与绘制逻辑  

```python
@ti.kernel
def compute_transform(angle: ti.f32):
    eye_pos = ti.Vector([0.0, 0.0, 5.0])
    model = get_model_matrix(angle)
    view = get_view_matrix(eye_pos)
    proj = get_projection_matrix(45.0, 1.0, 0.1, 50.0)
    mvp = proj @ view @ model

    for i in range(3):
        v = vertices[i]
        v4 = ti.Vector([v[0], v[1], v[2], 1.0])
        v_clip = mvp @ v4
        v_ndc = v_clip / v_clip[3]  # 透视除法
        screen_coords[i][0] = (v_ndc[0] + 1.0) / 2.0
        screen_coords[i][1] = (v_ndc[1] + 1.0) / 2.0

def main():
    vertices[0] = [2.0, 0.0, -2.0]
    vertices[1] = [0.0, 2.0, -2.0]
    vertices[2] = [-2.0, 0.0, -2.0]

    gui = ti.GUI("MVP Triangle", res=(600, 600))
    angle = 0.0

    while gui.running:
        angle += 0.5
        compute_transform(angle)
        a, b, c = screen_coords[0], screen_coords[1], screen_coords[2]
        gui.line(a, b, radius=2, color=0xFF0000)
        gui.line(b, c, radius=2, color=0x00FF00)
        gui.line(c, a, radius=2, color=0x0000FF)
        gui.show()
```

####  4.2 选做任务：3D 立方体透视旋转  
 4.2.1 立方体数据结构定义  

```python
vertices = ti.Vector.field(3, dtype=ti.f32, shape=8)
screen_coords = ti.Vector.field(2, dtype=ti.f32, shape=8)
edges = [
    (0, 1), (1, 2), (2, 3), (3, 0),  # 顶面
    (4, 5), (5, 6), (6, 7), (7, 4),  # 底面
    (0, 4), (1, 5), (2, 6), (3, 7)   # 竖边
]
# 初始化顶点（中心在原点，边长2）
vertices[0] = [1.0, 1.0, 1.0]
vertices[1] = [-1.0, 1.0, 1.0]
vertices[2] = [-1.0, 1.0, -1.0]
vertices[3] = [1.0, 1.0, -1.0]
vertices[4] = [1.0, -1.0, 1.0]
vertices[5] = [-1.0, -1.0, 1.0]
vertices[6] = [-1.0, -1.0, -1.0]
vertices[7] = [1.0, -1.0, -1.0]
```

 4.2.2 立方体渲染逻辑  

```python
while gui.running:
    angle += 0.5
    compute_transform(angle)
    # 绘制12条边
    edge_colors = [0xFF0000, 0xFF0000, 0xFF0000, 0xFF0000,
                   0x00FF00, 0x00FF00, 0x00FF00, 0x00FF00,
                   0x0000FF, 0x0000FF, 0x0000FF, 0x0000FF]
    for i, (v1, v2) in enumerate(edges):
        gui.line(screen_coords[v1], screen_coords[v2], radius=2, color=edge_colors[i])
    gui.show()
```

### <font style="color:rgb(0, 0, 0);background-color:rgba(0, 0, 0, 0);">五、实验结果与分析 </font><font style="color:rgb(0, 0, 0);background-color:rgba(0, 0, 0, 0);">📊</font>
#### <font style="color:rgb(0, 0, 0);background-color:rgba(0, 0, 0, 0);">5.1 基础任务结果</font>
<font style="color:rgb(0, 0, 0);background-color:rgba(0, 0, 0, 0);">成功实现了 3D 三角形的 MVP 变换与线框渲染：</font>

<font style="color:rgb(0, 0, 0);background-color:rgba(0, 0, 0, 0);">三角形绕 Z 轴自动旋转，视角稳定。</font>

<font style="color:rgb(0, 0, 0);background-color:rgba(0, 0, 0, 0);">三条边分别用红、绿、蓝三色绘制，边界清晰。</font>

<font style="color:rgb(0, 0, 0);background-color:rgba(0, 0, 0, 0);">透视效果明显，三角形在旋转过程中大小随深度变化。</font>

<img src="work1.gif" alt="三角形旋转效果" width="600" />

#### <font style="color:rgb(0, 0, 0);background-color:rgba(0, 0, 0, 0);">5.2 选做任务结果</font>
<font style="color:rgb(0, 0, 0);background-color:rgba(0, 0, 0, 0);">成功实现了 3D 立方体的透视旋转：</font>

<font style="color:rgb(0, 0, 0);background-color:rgba(0, 0, 0, 0);">立方体中心在原点，边长为 2，顶点坐标在</font>`<font style="color:rgb(0, 0, 0);background-color:rgba(0, 0, 0, 0);">[-1,1]</font>`<font style="color:rgb(0, 0, 0);background-color:rgba(0, 0, 0, 0);">之间。</font>

<font style="color:rgb(0, 0, 0);background-color:rgba(0, 0, 0, 0);">12 条边按顶面（红）、底面（绿）、竖边（蓝）区分，结构清晰。</font>

<font style="color:rgb(0, 0, 0);background-color:rgba(0, 0, 0, 0);">绕 Y 轴旋转时，立方体呈现出明显的 3D 空间感，近大远小的透视效果符合预期。</font>

<img src="work1.2.gif" alt="3D立方体旋转效果" width="600" />
