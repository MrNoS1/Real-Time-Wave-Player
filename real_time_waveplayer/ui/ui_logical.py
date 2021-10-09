import queue
import sys
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5 import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
import numpy as np
import sounddevice as sd
import soundfile as sf
from PyQt5.QtWidgets import QDialog, QMainWindow, QPushButton, QVBoxLayout, QApplication
from PyQt5.QtCore import QTimer
from os import listdir
from time import strftime, localtime
from real_time_waveplayer.ui.ui_business import Ui_MainWindow


class Mydemo(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(Mydemo, self).__init__()
        self.setupUi(self)
        self.figure = plt.figure(facecolor='black')

        self.canves = FigureCanvas(self.figure)
        self.canves_bar = NavigationToolbar(self.canves, self)
        self.verticalLayout.addWidget(self.canves)
        self.verticalLayout_bar.addWidget(self.canves_bar)

        # 信号和槽
        self.pushButton_save_close.setCheckable(True)
        self.pushButton_save_close.clicked.connect(self.save_close_wave)

        self.pushButton_auto_save_close.setCheckable(False)
        self.pushButton_auto_save_close.clicked.connect(self.auto_save_close_wave)

        self.pushButton_play.setCheckable(True)
        self.pushButton_play.clicked.connect(self.wave_play_close_open)

        self.pushButton_save_close.setEnabled(False)
        self.pushButton_auto_save_close.setEnabled(False)
        self.pushButton_play.setEnabled(False)

        self.pushButton_set.clicked.connect(self.init_set)
        self.pushButton_set.setCheckable(False)

        # 自启动学需要执行下面函数
        # self.init_set()
        # self.auto_save_close_wave()

    def init_set(self):
        # 逻辑参数
        self.channels = [1]
        self.device = None
        self.window = 200  #visible time slot
        self.interval = int(self.lineEdit_interval.text())
        self.blocksize = 0   # 默认
        self.samplerate = int(self.lineEdit_samplerate.text())  #     # lineEdit_samplerate
        self.downsample = int(self.LineEdit_downsample.text())    #  LineEdit_downsample
        self.subtype = None
        self.wave = None

        # 定义流
        self.stream_save_wave = sd.Stream(
            blocksize=self.blocksize,
            device=self.device,
            channels=max(self.channels),
            samplerate=self.samplerate,
            callback=self.audio_callback_save_wave)

        self.stream_real_time = sd.Stream(
            blocksize=self.blocksize,
            device=self.device,
            channels=max(self.channels),
            samplerate=self.samplerate,
            callback=self.audio_callback_real_time)

        # 绘图初始化
        self.length = int(self.window * self.samplerate / (1000 * self.downsample))
        self.plotdata = np.zeros((self.length, len(self.channels)))  # 一列是一根线， 总共channel 根线

        self.q_real_time = queue.Queue()
        if any(c < 1 for c in self.channels):  # 有个 0 就报错
            print('argument CHANNEL: must be >= 1')
        self.mapping = [c - 1 for c in self.channels]  # Channel numbers start with 1

        self.ax = self.figure.add_subplot()
        self.lines = self.ax.plot(self.plotdata)  #
        if len(self.channels) > 1:
            self.legend(['channel {}'.format(c) for c in self.channels],
                      loc='lower left', ncol=len(self.channels))
        self.ax.axis((0, len(self.plotdata), -1, 1))
        self.ax.set_yticks([0])
        self.ax.yaxis.grid(True)
        self.ax.tick_params(bottom=False, top=False, labelbottom=False,
                       right=False, left=False, labelleft=False)
        self.figure.tight_layout(pad=0)

        # 动态图线程
        self.ani = FuncAnimation(self.figure, self.update_plot, interval=self.interval, blit=True)
        # 按钮启用
        self.pushButton_save_close.setEnabled(True)
        self.pushButton_auto_save_close.setEnabled(True)
        self.pushButton_play.setEnabled(True)
        self.pushButton_set.setEnabled(False)

        # 循环全局变量


    def wave_play_close_open(self):
        if self.pushButton_play.isChecked():
            self.stream_real_time.start()
            print("显示波形")
            self.pushButton_play.setText("暂停显示")
        else:
            self.stream_real_time.stop()
            print("暂停显示")
            self.pushButton_play.setText("显示波形")

    def save_close_wave(self):
        if self.pushButton_save_close.isChecked():
            self.open_sound_file()
            print("button pressed  录制。。。。。。")
            self.pushButton_save_close.setText("停止录制")
        else:
            self.close_sound_file()
            print("button released 。。。。停止录制")
            self.pushButton_save_close.setText("开始录制")

    def open_sound_file(self):
        file_name = self.lineEdit_wave_filename.text() + '/' +str(len(listdir(self.lineEdit_wave_filename.text()))) + strftime("_realtime__%Y_%m_%d_%H_%M_%S.wav", localtime())
        self.pushButton_auto_save_close.setEnabled(False)
        self.file = sf.SoundFile(file_name, mode='x', samplerate=self.samplerate, channels=len(self.channels),
                            subtype=self.subtype)
        self.stream_save_wave.start()

    def close_sound_file(self):
        print("stop")
        self.stream_save_wave.stop()
        self.file.close()
        self.pushButton_auto_save_close.setEnabled(True)

    def auto_save_close_wave(self):    # 自动保存
        print("button pressed  自动录制。。。。。。")
        self.save_times = int(self.lineEdit_file_times.text())
        file_name = self.lineEdit_wave_filename.text() + '/' +str(len(listdir(self.lineEdit_wave_filename.text()))) + strftime("__%Y_%m_%d_%H_%M_%S.wav", localtime())  #str(len(listdir("time_wave"))) +
        auto_time = int(self.LineEdit_savetime.text()) * 1000  # 5000   # 自动录制时间
        self.pushButton_auto_save_close.setText("正在录制..." + str(self.save_times))
        self.pushButton_save_close.setEnabled(False)
        self.file = sf.SoundFile(file_name, mode='x', samplerate=self.samplerate, channels=len(self.channels),
                            subtype=self.subtype)
        self.stream_save_wave.start()
        qtimer = QTimer.singleShot(auto_time, self.auto_close_sound_file)

    def auto_close_sound_file(self):
        print("stop")
        self.stream_save_wave.stop()
        self.file.close()
        self.pushButton_auto_save_close.setText("自动录制")
        self.pushButton_save_close.setEnabled(True)
        if self.save_times > 1:
            self.save_times -= 1
            # self.auto_save_close_wave()
            print("button pressed  自动录制。。。。。。")
            file_name = self.lineEdit_wave_filename.text() + '/' +str(len(listdir(self.lineEdit_wave_filename.text()))) + strftime("__%Y_%m_%d_%H_%M_%S.wav", localtime())
            auto_time = int(self.LineEdit_savetime.text()) * 1000  # 5000   # 自动录制时间
            self.pushButton_auto_save_close.setText("正在录制..." + str(self.save_times))
            self.pushButton_save_close.setEnabled(False)
            self.file = sf.SoundFile(file_name, mode='x', samplerate=self.samplerate, channels=len(self.channels),
                                     subtype=self.subtype)
            self.stream_save_wave.start()
            qtimer = QTimer.singleShot(auto_time, self.auto_close_sound_file)


    def audio_callback_save_wave(self, indata, outdata, frames, time, status):
        """This is called (from a separate thread) for each audio block."""
        if status:
            print(status, file=sys.stderr)
        # Fancy indexing with mapping creates a (necessary!) copy:
        self.file.write(indata.copy())
        # print("writing------")

    def audio_callback_real_time(self, indata, outdata, frames, time, status):
        """This is called (from a separate thread) for each audio block."""
        if status:
            print(status, file=sys.stderr)
        # Fancy indexing with mapping creates a (necessary!) copy:
        self.q_real_time.put(indata[::self.downsample, self.mapping])

    def update_plot(self, frame):
        """This is called by matplotlib for each plot update.

        Typically, audio callbacks happen more frequently than plot updates,
        therefore the queue tends to contain multiple blocks of audio data.

        """
        while True:
            try:
                data = self.q_real_time.get_nowait()  # data是每次取出的新数据 长度根据Iostream的采用率， 每次返回的data长度一般比较小且不重复
            except queue.Empty:
                break
            shift = len(data)
            self.plotdata = np.roll(self.plotdata, -shift, axis=0)
            self.plotdata[-shift:, :] = data
        for column, line in enumerate(self.lines):
            line.set_ydata(self.plotdata[:, column])
        return self.lines