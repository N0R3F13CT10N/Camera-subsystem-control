# import the necessary packages
import numpy as np
import imutils
import cv2


class MotionDetector:
    def __init__(self, accumWeight=0.5):
        # храним аккумулируемый вес
        self.accumWeight = accumWeight

        # фоновая модель
        self.bg = None

    def update(self, image):
        # если модели нет, инициализируем
        if self.bg is None:
            self.bg = image.copy().astype("float")
            return

        # обновляем фоновую модель, аккумулируя вес
        cv2.accumulateWeighted(image, self.bg, self.accumWeight)

    def detect(self, image, tVal=25):
        # вычисляем абсолютную разность фоновой модели
        # и полученного изображения, затем применение порогового фильтра
        delta = cv2.absdiff(self.bg.astype("uint8"), image)
        thresh = cv2.threshold(delta, tVal, 255, cv2.THRESH_BINARY)[1]

        # преобразование изображения для устранения дефектов
        thresh = cv2.erode(thresh, None, iterations=2)
        thresh = cv2.dilate(thresh, None, iterations=2)

        # поиска контуров и иницализация области распознанного движения
        cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
                                cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        (minX, minY) = (np.inf, np.inf)
        (maxX, maxY) = (-np.inf, -np.inf)

        # если нет контуров, возвращаем None
        if len(cnts) == 0:
            return None

        # иначе цикл по контурам
        for c in cnts:
            # вычисление области распознанного движения
            (x, y, w, h) = cv2.boundingRect(c)
            (minX, minY) = (min(minX, x), min(minY, y))
            (maxX, maxY) = (max(maxX, x + w), max(maxY, y + h))

        # возврат кортежа с изображением и областью распознанного движения
        return thresh, (minX, minY, maxX, maxY)
