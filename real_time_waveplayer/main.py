import sys
from PyQt5.QtWidgets import QApplication
from real_time_waveplayer.ui.ui_logical import Mydemo
from real_time_waveplayer.utils.realwave import WavePlayer

if __name__ == '__main__':
    # 动态频谱
    player = WavePlayer(1024, 44100)
    # player.file_wave("D:/GIT_Notes/l.wav", blocksize=512, fs=44100)
    player.real_wave()

    # 示波器
    app = QApplication(sys.argv)
    demo = Mydemo()
    demo.show()
    sys.exit(app.exec_())

