import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA


def _cutdata4fft(arr, init=0):
    arr = arr[init:]
    ll = 2 ** (len(format(len(arr), 'b')) - 1)
    return arr[:ll]

def _lpfilter(fl, kc, rmdc=False):
    ll = len(fl)
    Fk = np.fft.fft(fl)
    Fk[kc+1:ll-kc] = 0
    if rmdc == True:
        Fk[0] = 0
    return np.real(np.fft.ifft(Fk))

def lpfilter(fl, cutoff_hz, samp_hz=1000, init=0, rmdc=False):
    '''
    Retern lowpass filtering array of sampling array.

    Parameters
    ----------
    fl : one-dimensional numpy array
        Sampling data.
    cutoff_hz : int
        Cutoff frequency of lowpass filter.
    samp_hz : int, optional (1000)
        Sampling frequency. default value is 1000[Hz].
    init : int or float, optional (0)
        Initial time[sec]. Initial cutoff numbers of data is given by sampling-frequency times init.
    rmdc : bool, optional (False)
        Removal of direct-current.
    '''
    arr = _cutdata4fft(fl, int(init * samp_hz))
    arr_len = len(arr)
    if cutoff_hz >= samp_hz:
        return arr
    else:
        kc = int( np.round(cutoff_hz * arr_len / samp_hz) )
        return _lpfilter(arr, kc, rmdc)


class COP:
    '''
    COPインスタンスの生成.

    Parameters
    ----------
    fn : str, ファイル名
        重心動揺計から出力されたCSVデータ.
    cutoff_hz : int, optional (5)
        ローパスフィルタのカットオフ周波数.
    samp_hz : int, optional (100)
        重心動揺計のサンプリング周波数.
    init : int または float, optional (5)
        初期時刻.
    '''
    def __init__(self, fn, **kwargs):
        cutoff_hz = kwargs.get('cutoff_hz', 5)
        samp_hz   = kwargs.get('samp_hz', 100)
        init      = kwargs.get('init', 5)
        self.__fn = fn
        self.__cutoff_hz = cutoff_hz
        self.__samp_hz = samp_hz
        self.__init = init
        df0 = pd.read_csv(fn, encoding='shift_jis', header=None, nrows=6)
        df = pd.read_csv(fn, encoding='shift_jis', skiprows=7, header=None)
        r1 = lpfilter(np.array(df[1]), cutoff_hz, samp_hz=samp_hz, init=init, rmdc=False)
        r2 = lpfilter(np.array(df[2]), cutoff_hz, samp_hz=samp_hz, init=init, rmdc=False)
        self.__r = np.array([r1, r2]).T
        self.__len = len(r1)
        pca = PCA(n_components=2)
        pca.fit(self.__r)
        self.__df0 = df0
        self.__df = df.iloc[:,0:9]
        self.__pca = pca

    @property
    def file_name(self):
        '''
        Return str.
        COPデータの読み込みファイル名.
        '''
        return self.__fn

    @property
    def sampling_hz(self):
        '''
        Return int.
        COPデータのサンプリング周波数.
        '''
        return self.__samp_hz

    @property
    def cutoff_hz(self):
        '''
        Return int.
        COPインスタンスのローパスフィルタ・カットオフ周波数.
        '''
        return self.__cutoff_hz

    @property
    def initial_time(self):
        '''
        Rerurn float.
        COPインスタンスの初期時刻.
        '''
        return self.__init

    @property
    def length(self):
        '''
        Return int.
        COPインスタンスに含まれる各種データの長さ.
        '''
        return self.__len

    @property
    def personal_info(self):
        '''
        Return list.
        個人情報リスト.

        各インデックスの内容 ;
        0 : ID番号
        1 : 氏名
        2 : 性別 (m or f)
        3 : 年齢
        4 : 身長 [cm]
        5 : 体重 [kgw]
        6 : 開眼 or 閉眼
        '''
        lis = [self.__df0.iloc[0, 1]]
        if self.__df0.iloc[2,1 ] == '男':
            lis.append('m')
        elif self.__df0.iloc[2, 1] == '女':
            lis.append('f')
        else:
            lis.append('unknown')
        try:
            lis.append(int(float(self.__df0.iloc[3, 1])))
        except:
            lis.append(self.__df0.iloc[3, 1])
        try:
            lis.append(float(self.__df0.iloc[4, 1]))
        except:
            lis.append(self.__df0.iloc[4, 1])
        try:
            lis.append(float(self.__df0.iloc[5, 1]))
        except:
            lis.append(self.__df0.iloc[5, 1])
        if self.__df0.iloc[0,3] == '開眼':
            lis.append('sight')
        elif self.__df0.iloc[0,3] == '閉眼':
            lis.append('blind')
        else:
            lis.append('unknown')
        return lis

    @property
    def device_DF(self):
        '''
        Return pandas DataFrame.
        計測器から得られた生のデータフレーム.

        データフレームのフィールド;
        t : 実験時間 [sec]
        Cx : 総合COPのx座標 [cm]
        Cy : 総合COPのx座標 [cm]
        Lx : 左足COPのx座標 [cm]
        Ly : 左足COPのx座標 [cm]
        Lweight : 左足にかかる重量 [kgw]
        Rx : 右足COPのx座標 [cm]
        Ry : 右足COPのx座標 [cm]
        Rweight : 右足にかかる重量 [kgw]
        '''
        self.__df.columns=['t','Cx','Cy','Lx','Ly','Lweight','Rx','Ry','Rweight']
        return self.__df

    @property
    def device_r(self):
        '''
        Return numpy array.
        計測器COP位置ベクトルの時系列シリーズ.
        '''
        return self.__r

    @property
    def transformed_r(self):
        '''
        Return numpy array.
        主軸変換後のCOP位置ベクトルの時系列シリーズ.
        '''
        if self.__pca.components_[0,1] < 0:
            return -self.__pca.transform(self.__r)
        else:
            return self.__pca.transform(self.__r)

    @property
    def eigen_values(self):
        '''
        Return numpy array.
        COP点群の共分散行列の固有値.
        '''
        return self.__pca.explained_variance_

    @property
    def eigen_vector(self):
        '''
        Return numpy array.
        COP点群の共分散行列の固有値に属する固有ベクトル.
        '''
        if self.__pca.components_[0,1] < 0:
            return -self.__pca.components_
        else:
            return self.__pca.components_

    @property
    def rot_angle(self):
        '''
        Return float.
        計測器座標系と主軸座標系の角度差[rad].
        '''
        return np.pi/2 - np.arccos(self.eigen_vector[0,0])

    @property
    def contribution_ratio(self):
        '''
        Return numpy array.
        COP点群のそれぞれの主軸への因子寄与率.
        '''
        return self.__pca.explained_variance_ratio_

    @property
    def device_xy_range(self):
        '''
        Return numpy array.
        計測器座標系におけるCOP点群のxレンジとyレンジ.(xは左右方向，yは前後方向)
        '''
        r = self.device_r
        return np.max(r, axis=0) - np.min(r, axis=0)

    @property
    def xy_range(self):
        '''
        Return numpy array.
        主軸成分におけるCOP点群のxレンジとyレンジ.(xは前後方向，yは左右方向)
        '''
        r = self.transformed_r
        return np.max(r, axis=0) - np.min(r, axis=0)

    @property
    def device_xy_range_ratio(self):
        '''
        Return numpy array.
        計測器座標系におけるCOP点群のxレンジとyレンジのレンジの構成比率.(xは左右方向，yは前後方向)
        '''
        total_range = self.device_xy_range[0] + self.device_xy_range[1]
        return np.array([self.device_xy_range[0], self.device_xy_range[1]]) / total_range

    @property
    def xy_range_ratio(self):
        '''
        Return numpy array.
        主軸系におけるCOP点群のxレンジとyレンジの構成比率.(xは前後方向，yは左右方向)
        '''
        total_range = self.xy_range[0] + self.xy_range[1]
        return np.array([self.xy_range[0], self.xy_range[1]]) / total_range

    @property
    def device_rectangle_area(self):
        '''
        Return float.
        計測器座標系におけるCOP点群の矩形面積.
        '''
        r = self.device_r
        r_range = np.max(r, axis=0) - np.min(r, axis=0)
        return r_range[0] * r_range[1]

    @property
    def rectangle_area(self):
        '''
        Return float.
        主軸系におけるCOP点群の矩形面積.
        '''
        r = self.transformed_r
        r_range = np.max(r, axis=0) - np.min(r, axis=0)
        return r_range[0] * r_range[1]

    @property
    def trajectory_length(self):
        '''
        Return float.
        COP軌跡長.
        '''
        r = self.transformed_r
        x = r.T[0]
        y = r.T[1]
        return np.sqrt( np.sum(diff(x)**2 + diff(y)**2) )

    @property
    def xy_rms(self):
        '''
        Return numpy array.
        主軸成分におけるCOP点群のx方向RMSとy方向RMS.(xは前後方向，yは左右方向)
        '''
        return np.array(np.sqrt(self.eigen_values))

    @property
    def xy_rms_ellipse_area(self):
        '''
        Return float.
        主軸成分におけるCOP点群のx方向RMSとy方向RMSを軸とした楕円面積.(xは前後方向，yは左右方向)
        '''
        return np.pi * self.xy_rms[0] * self.xy_rms[1]


    def set_cutoff_hz(self, cutoff_hz):
        '''
        COPインスタンスのローパスフィルタ・カットオフ周波数の変更.

        Parameter
        ---------
        cutoff_hz : int
            ローパスフィルタのカットオフ周波数[Hz]
        '''
        print(f'カットオフ周波数が{self.__cutoff_hz}[Hz]から{cutoff_hz}[Hz]に変更されました.')
        self.__init__(self.__fn, cutoff_hz=cutoff_hz, init=self.__init)


    def set_initial_time(self, init):
        '''
        COPインスタンスの初期時刻の変更.

        Parameter
        ---------
        init : int or float, 小数第2位まで
            初期時刻[sec]
        '''
        print(f'初期時刻が{self.__init}[sec]から{init}[sec]に変更されました.')
        self.__init__(self.__fn, cutoff_hz=self.__cutoff_hz, init=init)


    def draw_trajectory(self, **kwargs):
        '''
        COP軌跡の描画.

        Parameters
        ----------
        istransformed : bool, optional (True)
            Falseの場合，重心動揺計座標系でのCOP軌跡を描画. デフォルト値はTrue.
        dpi : int, optional (150)
            解像度の指定. デフォルト値は150dpi.
        figsize : taple または list, optional ((5 ,5))
            グラフサイズの指定. デフォルト値は(5, 5).
        color : str, optional ('black')
            カラーの指定. デフォルト値は'black'.
        title : str, optional (None)
            グラフタイトルの指定. デフォルト値はNone.
        isMKS : bool, optional (False)
            MKS単位系の指定. デフォルトはCGS単位系. デフォルト値はFalse.
        islegend : bool, optional (False)
            凡例を付けるかどうか. デフォルトでは付けない. Trueの場合，xの凡例を付ける. デフォルト値はFalse.

        '''
        istransformed = kwargs.get('transformed', True)
        dpi           = kwargs.get('dpi', 150)
        figsize       = kwargs.get('figsize', (5, 5))
        color         = kwargs.get('color', 'black')
        title         = kwargs.get('title', None)
        isMKS         = kwargs.get('isMKS', False)
        islegend      = kwargs.get('islegend', False)
        if istransformed == False:
            r = self.device_r
            center = self.__pca.mean_
            range_min = np.min(r.T[1]) - center[1]
            range_max = np.max(r.T[1]) - center[1]
            legend_label = 'original r'
        else:
            r = self.transformed_r
            center = np.array([0, 0])
            range_min = np.min(r.T[0])
            range_max = np.max(r.T[0])
            legend_label = 'transformed r'
        if abs(range_min) > range_max:
            range_max = abs(range_min)
        range_lim = range_max * 1.25
        x = r.T[0]
        y = r.T[1]
        xlab = 'x[cm]'
        ylab = 'y[cm]'
        if isMKS == True:
            x = x / 100
            y = y / 100
            range_lim = range_lim /100
            xlab = 'x[m]'
            ylab = 'y[m]'
        plt.figure(dpi=dpi, figsize=figsize)
        plt.plot(x, y, color=color)
        plt.xlim(-range_lim + center[0], range_lim + center[0])
        plt.ylim(-range_lim + center[1], range_lim + center[1])
        plt.xlabel(xlab)
        plt.ylabel(ylab)
        if islegend == True:
            plt.legend([legend_label])
        if title != None:
            plt.title(title, loc='left')
        plt.grid()
        plt.show()


    def draw_time_series(self, **kwargs):
        '''
        COP時系列の描画.

        Parameters
        ----------
        dpi : int, optional (150)
            解像度の指定. デフォルト値は150dpi.
        figsize : taple または list, optional ((5, 5))
            グラフサイズの指定. デフォルト値は(5, 5).
        color : str, optional ('black')
            カラーの指定. デフォルト値は'black'.
        title : str, optional (None)
            グラフタイトルの指定. デフォルト値はNone.
        isMKS : bool, optional (False)
            MKS単位系の指定. デフォルトはCGS単位系. デフォルト値はFalse.
        islegend : bool, optional (True)
            凡例を付けるかどうか. デフォルトでは付ける. Falseの場合，凡例を付けない. デフォルト値はTrue.
        isdrawy : bool, optional (True)
            Falseの場合，y成分を描画しない. デフォルト値はTrue.
        '''
        dpi      = kwargs.get('dpi', 150)
        figsize  = kwargs.get('figsize', (10,5))
        color    = kwargs.get('color', ('black','gray'))
        title    = kwargs.get('title', None)
        isMKS    = kwargs.get('isMKS', False)
        islegend = kwargs.get('islegend', True)
        isdrawy  = kwargs.get('isdrawy', True)
        r = self.transformed_r
        x = r.T[0]
        y = r.T[1]
        ylab = 'COP[cm]'
        range_min = np.min(x)
        range_max = np.max(x)
        if abs(range_min) > range_max:
            range_max = abs(range_min)
        range_lim = range_max * 1.25
        if isMKS == True:
            x = x / 100
            y = y / 100
            range_lim = range_lim / 100
            ylab = 'COP[m]'
        plt.figure(dpi=dpi, figsize=figsize)
        plt.plot(x, color=color[0])
        if isdrawy == True:
            plt.plot(y, color=color[1])
        plt.ylim([-range_lim, range_lim])
        plt.ylabel(ylab)
        seq_list = np.arange(0, self.__len, self.__samp_hz * 5)
        time_list = np.arange(self.__init, self.__len//self.__samp_hz + self.__init + 1, 5)
        plt.xticks(seq_list, time_list)
        plt.xlabel('time[sec]')
        if islegend == True:
            if isdrawy == True:
                plt.legend(['x', 'y'])
            else:
                plt.legend(['x'])
        if title != None:
            plt.title(title, loc='left')
        plt.grid()
        plt.show()
