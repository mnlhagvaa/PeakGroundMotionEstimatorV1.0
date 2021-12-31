import sys
from PyQt5 import uic, QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QMessageBox, QLabel, QCheckBox
from obspy.clients.fdsn import Client
from obspy import read, UTCDateTime
import datetime
import pyqtgraph as pg
import pandas as pd
import numpy as np
from pyqtgraph import PlotWidget
g=980.665
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs ):
        super(MainWindow, self).__init__(*args, **kwargs)                                              # Call the inherited classes __init__ method
        uic.loadUi('gui_dataav.ui', self)      # Load the .ui file
        self.pushButton.clicked.connect(self.button_clicked)                    # check if button is clicked, if YES call function button_clicked
        self.pushButton_2.clicked.connect(self.button_clicked_pga)

    def button_clicked_pga(self):
        net = self.comboBox.currentText()                                                # get Network from user and assign it to variable net
        sta = self.comboBox_2.currentText()                                              # get Station from user and assign it to variable Sta
        loc = self.comboBox_3.currentText()                                              # get Location from user and assign it to variable Loc
        if (loc == "--"):
            loc = ''
        chan= self.comboBox_4.currentText()                                              # get Channel from user and assign it to variable Chan
        startdate  = self.dateTimeEdit.dateTime().toPyDateTime()                                     # get starttime from user and assign it to variable starttime
        enddate    = self.dateTimeEdit_2.dateTime().toPyDateTime()                                   # get endtime from user and assign it to variable endtime
        st = self.get_wf(net, sta, loc, chan, startdate, enddate)
        self.est_pga(st)
    def est_pga(self, st):
        st.merge()
        column1, column2, column3 = [], [], []
        #df = pd.DataFrame(columns=["STATION ID", "PGA [m/s**2]", "PGA [g]"])
        for tr in st:
            sta_id = tr.get_id()
            sensi = tr.stats.response.instrument_sensitivity.value
            in_unit = tr.stats.response.instrument_sensitivity.input_units
            if isinstance(tr.data, np.ma.core.MaskedArray):
                st_umask = tr.split()
                a = []
                for tr1 in st_umask:
                    tr1.detrend("demean")
                    tr1.detrend("linear")
                    if in_unit == "m/s" or in_unit == "M/S":
                        tr1.data = np.gradient(tr1.data, tr1.stats.delta)
                        tr1.remove_sensitivity()
                        a.append(abs(max(tr1.data)))
                        amax = max(a)

                    elif in_unit == "m/s**2" or "M/S**2":
                        tr1.remove_sensitivity()
                        a.append(abs(max(tr1.data)))
                        amax = max(a)
                column1.append(sta_id)
                column2.append(amax*100)           ## cm/s**2
                column3.append(amax*100/g)               ## g
                #print(tr1.stats.endtime, tr1.stats.station, tr1.stats.channel, amax)

            else:
                if in_unit == "m/s" or in_unit == "M/S":
                    tr.detrend("demean")
                    tr.detrend("linear")
                    tr.data = np.gradient(tr.data, tr.stats.delta)
                    tr.remove_sensitivity()
                    amax = abs(max(tr.data))
                elif in_unit == "m/s**2" or "M/S**2":
                    tr.detrend("demean")
                    tr.detrend("linear")
                    tr.remove_sensitivity()
                    amax = abs(max(tr.data))
                #print(tr.stats.endtime, tr.stats.station, tr.stats.channel, amax)
                column1.append(sta_id)
                column2.append(amax*100 )
                column3.append(amax*100/g)
        dict = {'STATION ID': column1, 'PGA [cm/s**2]': column2, 'PGA [g]': column3}
        df = pd.DataFrame(dict)
        self.print_pga(df)
    def clickMethod(self):
        QMessageBox.about(self, "Алдаа", "Таны хүсэлт хоосон байна. Та Станцын нэр, суваг, сүлжээ, хугацаагаа дахин шалгана уу !!!")

    def SetPlot(self, st):
        self.app = pg.mkQApp("Waveform Plotter")
        self.view = pg.GraphicsView()
        # view = pg.PlotWidget(axisItems = {'bottom': pg.DateAxisItem()})
        self.l = pg.GraphicsLayout(border=(100, 100, 100))
        self.view.setCentralItem(self.l)
        self.view.show()
        self.view.setWindowTitle('Waveform Plotter')
        self.view.resize(800, 600)
        self.view.setBackground('w')
        st.merge(fill_value=0)
        for tr in st:
            sensi = tr.stats.response.instrument_sensitivity.value
            in_unit = tr.stats.response.instrument_sensitivity.input_units
            #if in_unit == "m/s":
            #    data = np.gradient(tr.data, tr.stats.delta)
            x = np.linspace(UTCDateTime(tr.stats.starttime).timestamp, UTCDateTime(tr.stats.endtime).timestamp,
                            tr.stats.npts, endpoint=False)
            #### plot ####
            self.p1 = self.l.addPlot(axisItems={'bottom': pg.DateAxisItem(utcOffset=0)},
                                     title=tr.stats.network + "." + tr.stats.station + "." + tr.stats.location + "." + tr.stats.channel)
            self.p1.plot(x, tr.data, pen=pg.mkPen('k', width=1))
            self.l.nextRow()
            # # # # # # # #

    def button_clicked(self):
        net = self.comboBox.currentText()                                                # get Network from user and assign it to variable net
        sta = self.comboBox_2.currentText()                                              # get Station from user and assign it to variable Sta
        loc = self.comboBox_3.currentText()                                              # get Location from user and assign it to variable Loc
        if (loc == "--"):
            loc = ''
        chan= self.comboBox_4.currentText()                                              # get Channel from user and assign it to variable Chan
        startdate  = self.dateTimeEdit.dateTime().toPyDateTime()                                     # get starttime from user and assign it to variable starttime
        enddate    = self.dateTimeEdit_2.dateTime().toPyDateTime()                                   # get endtime from user and assign it to variable endtime
        st = self.get_wf(net, sta, loc, chan, startdate, enddate)
        self.SetPlot(st)
    def get_wf(self, net, sta, loc, chan, starttime, endtime):
        #client = Client("IRIS")
        host = ("http://192.168.56.11:8080")
        client = Client(host)
        try:
            st = client.get_waveforms(net, sta, loc, chan, UTCDateTime(starttime), UTCDateTime(endtime), attach_response=True)
            return st
        except:
            self.clickMethod()
            #sys.exit()

    def print_pga(self, df):
        df1 = df.to_string(col_space=20, justify="justify", index=False)
        self.textBrowser.setWordWrapMode(QtGui.QTextOption.NoWrap)
        self.textBrowser.setFont(QtGui.QFont("Monospace"))
        self.textBrowser.setText(df1)
        self.textBrowser.showMaximized()

    def date2jul (self, simpledate):
        stdate=simpledate.timetuple()
        jdateyear=int('%d%03d' % (stdate.tm_year, stdate.tm_yday))
        return jdateyear

    def jul2date (self, jdate):
        fmt = '%Y%j'
        datestd = datetime.datetime.strptime(jdate, fmt).date()
        return datestd

    def jul2timestamp(self, jdate):
        fmt = '%Y%j'
        datestd = datetime.datetime.strptime(jdate, fmt).date().strftime("%Y-%m-%d")
        datestd=datetime.datetime.strptime(datestd, "%Y-%m-%d").replace(tzinfo=datetime.timezone.utc).timestamp()
        return datestd

app = QtWidgets.QApplication(sys.argv) # Create an instance of QtWidgets.QApplication
window = MainWindow() # Create an instance of our class
window.show()
app.exec_() # Start the application
