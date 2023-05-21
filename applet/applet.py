import sys, csv, os, random
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QComboBox, QLineEdit, QPushButton, QMessageBox, QVBoxLayout, QHBoxLayout, QCheckBox
from PyQt5 import QtCore


class Widget(QWidget):

    def __init__(self):
        super().__init__()

        self.ips = []
        self.gateways = []
        self.eds = []

        # Read the devices file and populate the arrays
        with open('devices.txt', 'r') as f:
            for line in f:
                ip, device = line.strip().split()
                self.ips.append(ip)
                if device == "GW":
                    self.gateways.append(ip)
                else:
                    self.eds.append(ip)

        self.initUI()

    def initUI(self):
        devices = ["ED", "GW"]

        # create labels for the drop-down fields
        label1 = QLabel('#ED/GW:', self)

        # create drop-down fields and populate them with options from the arrays
        self.comboBox1 = QComboBox(self)
        self.comboBox1.addItems(devices)
        self.comboBox1.currentIndexChanged.connect(self.showFields)

        # create labels and text fields for the fill-in fields
        self.label1 = QLabel('Time:', self)
        self.lineEdit1 = QLineEdit(self)
        self.lineEdit1.setFixedWidth(70)
        

        self.label2 = QLabel('Packet size:', self)
        self.lineEdit2 = QLineEdit(self)
        self.lineEdit2.setFixedWidth(70)

        self.label3 = QLabel('Period:', self)
        self.lineEdit3 = QLineEdit(self)
        self.lineEdit3.setFixedWidth(70)

        self.label6 = QLabel(
            f'{len(self.eds)} devices available. How many with spreading factor of 7?', self)
        self.lineEdit6 = QLineEdit(self)
        self.lineEdit6.setFixedWidth(70)

        self.label7 = QLabel(
            f'{len(self.eds)} devices available. How many with spreading factor of 8?', self)
        self.lineEdit7 = QLineEdit(self)
        self.lineEdit7.setFixedWidth(70)

        self.label8 = QLabel(
            f'{len(self.eds)} devices available. How many with spreading factor of 9?', self)
        self.lineEdit8 = QLineEdit(self)
        self.lineEdit8.setFixedWidth(70)
        

        self.label9 = QLabel(
            f'{len(self.eds)} devices available. How many with spreading factor of 10?', self)
        self.lineEdit9 = QLineEdit(self)
        self.lineEdit9.setFixedWidth(70)

        self.label10 = QLabel(
            f'{len(self.eds)} devices available. How many with spreading factor of 11?', self)
        self.lineEdit10 = QLineEdit(self)
        self.lineEdit10.setFixedWidth(70)

        self.label11 = QLabel(
            f'{len(self.eds)} devices available. How many with spreading factor of 12?', self)
        self.lineEdit11 = QLineEdit(self)
        self.lineEdit11.setFixedWidth(70)

        self.label4 = QLabel('rx2sf:', self)
        self.lineEdit4 = QLineEdit(self)
        self.lineEdit4.setFixedWidth(70)

        self.label5 = QLabel('confirmed:', self)
        self.checkBox1 = QCheckBox(self)
        self.checkBox1.stateChanged.connect(self.updateConfirmed)
        self.confirmed = 0

        self.success_label = QLabel('', self)

        # create button to write data to file
        button = QPushButton('Write to File', self)
        button.clicked.connect(self.writeToFile)

        

        # create layouts to organize widgets
        mainLayout = QVBoxLayout()
        topLayout = QHBoxLayout()
        
        self.fieldLayout = QVBoxLayout()
        

        # add widgets to layouts
        topLayout.addWidget(label1)
        topLayout.addWidget(self.comboBox1)
        # topLayout.addWidget(label2)
        # topLayout.addWidget(self.comboBox2)
        

        self.fieldLayout.addWidget(self.label1)
        self.fieldLayout.addWidget(self.lineEdit1)
        self.fieldLayout.addWidget(self.label2)
        self.fieldLayout.addWidget(self.lineEdit2)
        self.fieldLayout.addWidget(self.label3)
        self.fieldLayout.addWidget(self.lineEdit3)

        self.fieldLayout.addWidget(self.label4)
        self.fieldLayout.addWidget(self.lineEdit4)

        # self.fieldLayout.addWidget(self.lineEdit5)

        self.fieldLayout.addWidget(self.label6)
        self.fieldLayout.addWidget(self.lineEdit6)
        self.fieldLayout.addWidget(self.label7)
        self.fieldLayout.addWidget(self.lineEdit7)
        self.fieldLayout.addWidget(self.label8)
        self.fieldLayout.addWidget(self.lineEdit8)
        self.fieldLayout.addWidget(self.label9)
        self.fieldLayout.addWidget(self.lineEdit9)
        self.fieldLayout.addWidget(self.label10)
        self.fieldLayout.addWidget(self.lineEdit10)
        self.fieldLayout.addWidget(self.label11)
        self.fieldLayout.addWidget(self.lineEdit11)
        self.fieldLayout.addWidget(self.label5)
        self.fieldLayout.addWidget(self.checkBox1)
        mainLayout.addWidget(self.success_label)

        

        mainLayout.addLayout(topLayout)
        mainLayout.addLayout(self.fieldLayout)
        # mainLayout.addWidget(self.tableWidget)
        topLayout.addWidget(button)

        # set main layout
        self.setLayout(mainLayout)

        # set window size and title
        self.setGeometry(300, 300, 450, 650)
        self.setWindowTitle('assets')

        # show the window
        self.show()

    def updateConfirmed(self, state):
        if state == QtCore.Qt.Checked:
            self.confirmed = 1
        else:
            self.confirmed = 0

    def showFields(self):
        # get the selected value from the first drop-down field
        selected_value = self.comboBox1.currentText()

        # show/hide the appropriate fill-in fields based on the selected value
        if selected_value == 'ED':

            self.setFixedSize(450, 650)
            self.label1.show()
            self.lineEdit1.show()
            self.label2.show()
            self.lineEdit2.show()
            self.label3.show()
            self.lineEdit3.show()
            # self.label4.setText('period:')
            # self.lineEdit4.show()
            self.label6.setText(
                f'{len(self.eds)} device(s) available. How many with spreading factor of 7?')
            sf7 = self.lineEdit6.show()
            self.label7.setText(
                f'{len(self.eds)} device(s) available. How many with spreading factor of 8?')
            sf8 = self.lineEdit7.show()
            self.label8.setText(
                f'{len(self.eds)} device(s) available. How many with spreading factor of 9?')
            sf9 = self.lineEdit8.show()
            self.label9.setText(
                f'{len(self.eds)} device(s) available. How many with spreading factor of 10?')
            sf10 = self.lineEdit9.show()
            self.label10.setText(
                f'{len(self.eds)} device(s) available. How many with spreading factor of 11?')
            sf11 = self.lineEdit10.show()
            self.label11.setText(
                f'{len(self.eds)} device(s) available. How many with spreading factor of 12?')
            sf12 = self.lineEdit11.show()
            self.label4.setText('rx2sf:')
            self.lineEdit4.show()
            self.label5.show()
            self.checkBox1.show()

            self.lineEdit1.show()
            self.lineEdit2.show()
            self.label3.show()
            self.label4.show()
            self.label5.show()
            self.lineEdit3.show()

        elif selected_value == 'GW':

            self.setFixedSize(450, 450)
            self.comboBox2 = QComboBox(self)
            self.comboBox2.addItems(self.gateways)
            self.lineEdit1.hide()
            self.label1.hide()
            self.lineEdit2.hide()
            self.label2.hide()
            self.lineEdit3.hide()
            self.label3.hide()
            self.label6.setText(
                f'{len(self.gateways)} device(s) available. How many with spreading factor of 7?')
            gw_sf7 = self.lineEdit6.show()
            self.label7.setText(
                f'{len(self.gateways)} device(s) available. How many with spreading factor of 8?')
            gw_sf8 = self.lineEdit7.show()
            self.label8.setText(
                f'{len(self.gateways)} device(s) available. How many with spreading factor of 9?')
            gw_sf9 = self.lineEdit8.show()
            self.label9.setText(
                f'{len(self.gateways)} device(s) available. How many with spreading factor of 10?')
            gw_sf10 = self.lineEdit9.show()
            self.label10.setText(
                f'{len(self.gateways)} device(s) available. How many with spreading factor of 11?')
            gw_sf11 = self.lineEdit10.show()
            self.label11.setText(
                f'{len(self.gateways)} device(s) available. How many with spreading factor of 12?')
            gw_sf12 = self.lineEdit11.show()
            self.label4.setText('rx2sf:')
            self.lineEdit4.show()

            self.label5.hide()
            self.lineEdit6.show()
            self.label6.show()
            self.lineEdit7.show()
            self.label7.show()

            self.checkBox1.hide()

    def writeToFile(self):
        selected_value = self.comboBox1.currentText()
        # get the data from the fields
        # field1 = self.comboBox1.currentText()
        # field2 = self.comboBox2.currentText()
        try:
            time = int(self.lineEdit1.text())
            pkt_size = int(self.lineEdit2.text())
            period = int(self.lineEdit3.text())
            rx2sf = int(self.lineEdit4.text())
        except ValueError:
            QMessageBox.warning(
                self, 'Error', 'Please enter a valid integer')
            return

        header = '#ED ip time(sec) pkt_size period sf rx2sf confirmed / GW ip sf rx2sf\n'
        # write the data to a CSV file
        with open('assets.txt', 'a') as file:
            if os.path.getsize('assets.txt') == 0:
                file.write(header)
            writer = csv.writer(file, delimiter=' ')
            if selected_value == "ED":
                try:
                    sf7 = int(self.lineEdit6.text() or 0)
                    sf8 = int(self.lineEdit7.text()or 0)
                    sf9 = int(self.lineEdit8.text()or 0)
                    sf10 = int(self.lineEdit9.text()or 0)
                    sf11 = int(self.lineEdit10.text()or 0)
                    sf12 = int(self.lineEdit11.text()or 0)
                except ValueError:
                    QMessageBox.warning(
                        self, 'Error', 'Please enter a valid integer')
                    return
                
                total_sfs = sf7 + sf8 + sf9 + sf10 + sf11 + sf12
                if (total_sfs > len(self.eds)):
                    QMessageBox.warning(
                        self, 'Error', 'Please enter a valid number not exceeding the number of devices available')
                    
                    return
                
                unchosen_ips = self.eds.copy()
                    
                for _ in range(total_sfs):

                    ip_ed = random.choice(unchosen_ips)
                    unchosen_ips.remove(ip_ed)
                    if sf7 != 0:
                        for i in range(sf7):
                            writer.writerow(
                        ["ED", ip_ed, time, pkt_size, period, 7, rx2sf, self.confirmed])
                            sf7-=1
                        continue

                    if sf8 != 0:
                        for i in range(sf8):
                            writer.writerow(
                        ["ED", ip_ed, time, pkt_size, period, 8, rx2sf, self.confirmed])
                            sf8-=1
                        continue
                    if sf9 != 0:
                        for i in range(sf9):
                            writer.writerow(
                        ["ED", ip_ed, time, pkt_size, period, 9, rx2sf, self.confirmed])
                            sf9-=1
                        continue
                    if sf10 != 0:
                        for i in range(sf10):
                            writer.writerow(
                        ["ED", ip_ed, time, pkt_size, period, 10, rx2sf, self.confirmed])
                            sf10-=1
                        continue
                    if sf11 != 0:
                        for i in range(sf11):
                            writer.writerow(
                        ["ED", ip_ed, time, pkt_size, period, 11, rx2sf, self.confirmed])
                            sf11-=1
                        continue
                    if sf12 != 0:
                        for i in range(sf12):
                            writer.writerow(
                        ["ED", ip_ed, time, pkt_size, period, 12, rx2sf, self.confirmed])
                            sf12-=1
                        continue
                

                    
            elif selected_value == "GW":
                try:
                    gw_sf7 = int(self.lineEdit6.text() or 0)
                    gw_sf8 = int(self.lineEdit7.text() or 0)
                    gw_sf9 = int(self.lineEdit8.text() or 0)
                    gw_sf10 = int(self.lineEdit9.text() or 0)
                    gw_sf11 = int(self.lineEdit10.text() or 0)
                    gw_sf12 = int(self.lineEdit11.text()or 0)
                except ValueError:
                    QMessageBox.warning(
                        self, 'Error', 'Please enter a valid integer')
                    return
                
                total_sf_gw = gw_sf7 + gw_sf8 + gw_sf9 + gw_sf10 + gw_sf11 + gw_sf12

                if (total_sf_gw> len(self.gateways)):
                    QMessageBox.warning(
                        self, 'Error', 'Please enter a valid number')
                    return
                unchosen_ips_gw = self.gateways.copy()

                for _ in range(total_sf_gw):
                    gw_ip = random.choice(unchosen_ips_gw)
                    unchosen_ips_gw.remove(gw_ip)
                    if gw_sf7 != 0:
                        for i in range(gw_sf7):
                            writer.writerow(["GW", gw_ip, 7, rx2sf])
                            gw_sf7-=1
                        continue
                    if gw_sf8 != 0:
                        for i in range(gw_sf8):
                            writer.writerow(["GW", gw_ip, 8, rx2sf])
                            gw_sf8-=1
                        continue
                    if gw_sf9 != 0:
                        for i in range(gw_sf9):
                            writer.writerow(["GW", gw_ip, 9, rx2sf])
                            gw_sf9-=1
                        continue
                    if gw_sf10 != 0:
                        for i in range(gw_sf10):
                            writer.writerow(["GW", gw_ip, 10, rx2sf])
                            gw_sf10-=1
                        continue
                    if gw_sf11 != 0:
                        for i in range(gw_sf11):
                            writer.writerow(["GW", gw_ip, 11, rx2sf])
                            gw_sf11-=1
                        continue
                    if gw_sf12 != 0:
                        for i in range(gw_sf12):
                            writer.writerow(["GW", gw_ip, 12, rx2sf])
                            gw_sf12-=1
                        continue

        self.comboBox1.setCurrentIndex(0)
        
        self.lineEdit1.clear()
        self.lineEdit2.clear()
        self.lineEdit3.clear()
        self.lineEdit4.clear()
        
        self.lineEdit6.clear()
        self.lineEdit7.clear()
        self.lineEdit8.clear()
        self.lineEdit9.clear()
        self.lineEdit10.clear()
        self.lineEdit11.clear()

        self.checkBox1.setChecked(0)

        self.success_label.setText('Added successfully.')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Widget()
    sys.exit(app.exec_())
