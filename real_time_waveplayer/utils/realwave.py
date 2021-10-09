import queue
import numpy as np
import sounddevice as sd
import soundfile as sf
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.ticker import FuncFormatter

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False


class WavePlayer():
    def __init__(self, blocksize, samplerate):
        self.blocksize = blocksize
        self.device = None,
        self.channels = 1,
        self.samplerate = samplerate
        self.q_real_time = queue.Queue()
        self.stream = sd.Stream(blocksize=self.blocksize,
                                device=None,
                                channels=1,
                                samplerate=self.samplerate,
                                callback=self.audio_callback)
        self.window = 200
        self.contrast = 20
        self.out_data = np.zeros((int(self.blocksize/2), self.window))
        self.out_data[:, -1] = self.contrast

    def audio_callback(self, indata, outdata, frames, time, status):
        self.q_real_time.put(np.abs(np.fft.fft(indata.reshape(-1))).reshape(-1, 1)[0:int(self.blocksize/2), :])

    def real_wave(self):
        fig_real = plt.figure()
        ax_real = fig_real.add_subplot(111)
        formatter_y = FuncFormatter(lambda x, pos: '%1.2fHz' % (x*self.samplerate/self.blocksize))
        formatter_x = FuncFormatter(lambda x, pos: '%1.2fs' % (x * self.blocksize/self.samplerate))
        ax_real.yaxis.set_major_formatter(formatter_y)
        ax_real.xaxis.set_major_formatter(formatter_x)
        ax_real.set_title("Spectrum")
        ax_real.set_xlabel("time")
        ax_real.set_ylabel("frequency")
        self.im_real = ax_real.imshow(self.out_data, animated=True, cmap='jet')
        ani_real = animation.FuncAnimation(fig_real, self.updatefig_real, interval=0, blit=True)
        with self.stream:
            plt.show()

    def updatefig_real(self, *args):
        try:
            data = self.q_real_time.get_nowait()
            self.out_data = np.roll(self.out_data, -1, axis=1)
            self.out_data[:, -1:] = data
            self.im_real.set_array(self.out_data)
        except queue.Empty:
            pass
        return self.im_real,

    def wave_fft(self, y_t, Fs, N):
        y = np.fft.fft(y_t)
        x_f = np.arange(int(N / 2)) * Fs / N
        y_f = np.abs(y[0:int(N / 2)]) * 2 / N
        return y_f.reshape(-1, 1)

    def file_wave(self, filename, blocksize, fs):
        f_b = sf.blocks(filename, blocksize=blocksize, fill_value=0)
        f_b_list = [self.wave_fft(i, Fs=fs, N=blocksize) for i in f_b]
        f_t = np.concatenate(f_b_list, axis=1)

        fig = plt.figure()
        formatter_y = FuncFormatter(lambda y, pos: '%1.2fHz' % (y * fs/blocksize))
        formatter_x = FuncFormatter(lambda x, pos: '%1.2fs' % (x * blocksize/fs))
        ax = fig.add_subplot(111)
        ax.yaxis.set_major_formatter(formatter_y)
        ax.xaxis.set_major_formatter(formatter_x)
        ax.set_title("Spectrum")
        ax.set_xlabel("time")
        ax.set_ylabel("frequency")
        ax.imshow(f_t, cmap='jet')
        plt.show()
        return f_b_list
