import matplotlib.pyplot as plt # plt 用于显示图片
import matplotlib.image as mpimg # mpimg 用于读取图片

def showPicture():
    img1 = mpimg.imread('money1.png')  # 读取和代码处于同一目录下的 lena.png
    img2 = mpimg.imread('money2.jpg')

    # 结果展示
    plt.rcParams['font.sans-serif'] = ['SimHei']  # 中文乱码
    plt.subplot(121)
    # imshow()对图像进行处理，画出图像，show()进行图像显示
    plt.imshow(img1)

    plt.title('图像1')
    # 不显示坐标轴
    plt.axis('off')

    # 子图2
    plt.subplot(122)
    plt.imshow(img2)
    plt.title('图像2')
    plt.axis('off')

    # #设置子图默认的间距
    plt.tight_layout()
    # 显示图像
    plt.show()

showPicture()

