import pyfirmata


class ServosControl:
    def __init__(self):
        # инициализация микроконтроллера Arduino и сервоприводов
        board = pyfirmata.Arduino('COM3')
        self.vert_drive = board.digital[3]
        self.horiz_drive = board.digital[5]
        self.vert_drive.mode = pyfirmata.SERVO
        self.horiz_drive.mode = pyfirmata.SERVO
        self.reset()

# функции управления приводами
    def reset(self):
        self.vert_drive.write(90)
        self.horiz_drive.write(90)

    def rotate_left(self):
        if self.horiz_drive.read() < 180:
            self.horiz_drive.write(int(self.horiz_drive.read() + 1))

    def rotate_right(self):
        if self.horiz_drive.read() > 0:
            self.horiz_drive.write(int(self.horiz_drive.read() - 1))

    def rotate_down(self):
        if self.vert_drive.read() < 180:
            self.vert_drive.write(int(self.vert_drive.read() + 1))

    def rotate_up(self):
        if self.vert_drive.read() > 0:
            self.vert_drive.write(int(self.vert_drive.read() - 1))
