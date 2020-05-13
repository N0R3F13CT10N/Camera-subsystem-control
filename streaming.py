from motion_detector import MotionDetector
from servos_control import ServosControl
from imutils.video import VideoStream
from flask import Response, jsonify
from flask import Flask
from flask import render_template
import threading
import imutils
import time
import cv2

# инициализация отображаемого кадра и lock для многопоточности
# при трансляции на разные окна браузера или устройства
outputFrame = None
lock = threading.Lock()

# инициализация приложения Flask
app = Flask(__name__)

# инициализация видеопотока, двухсекундная задержка для инициализации
vs = VideoStream(src=0).start()
time.sleep(2.0)
sc = ServosControl()
# флаг фокусировки на движении
motion_focus = False
# координаты центра зоны распознанного движения
last_captured = [-1, -1]
# флаги занятости сервоприводов
in_progress_hor, in_progress_vert = False, False
delay = 0


# отображение главной страницы по дефолтному руту
@app.route("/")
def index():
    return render_template("index.html")


# наведение на зону распознанного движения
def aim_motion():
    global last_captured, in_progress_hor, in_progress_vert, delay
    # если есть координаты по оси X для наведения
    if last_captured[0] > -1:
        # если коодинаты в правой части изображения
        if last_captured[0] > 230:
            # смещение координаты в соответствии с пропорцией
            last_captured[0] -= 12
            # поворот камеры вправо
            sc.rotate_right()
        else:
            # аналогично с левой частью
            if last_captured[0] < 170:
                last_captured[0] += 12
                sc.rotate_left()
            else:
                # иначе наведение завершено, удаляются координаты
                # и меняется флаг занятости
                last_captured[0] = -1
                in_progress_hor = False
                delay = time.time()
    # аналогично с осью Y
    if last_captured[1] > -1:
        if last_captured[1] > 170:
            last_captured[1] -= 10
            sc.rotate_down()
        else:
            if last_captured[1] < 130:
                last_captured[1] += 10
                sc.rotate_up()
            else:
                last_captured[1] = -1
                in_progress_vert = False
                delay = time.time()


# обновление кадра и разпознавание движения
def frame_update(frameCount):
    global vs, outputFrame, lock, last_captured, motion_focus, in_progress_hor, in_progress_vert, delay

    md = MotionDetector(accumWeight=0.1)
    # число кадров
    total = 0

    # цикл обработки кадра
    while True:
        # получаем кадр из видеопотока, изменяем размер
        # конвертируем в GRAY и применяем фильтр Гаусса
        frame = vs.read()
        frame = imutils.resize(frame, width=400)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (7, 7), 0)


        #
        # если число кадров достигло нужного числа для создания фоновой модели
        # продолжаем обработку
        if total > frameCount:
            # пытаемся распознать движение
            motion = md.detect(gray)
            # если движение найдено
            if motion is not None:
                # распаковываем кортеж, выделяем зону прямоугольником
                thresh, (minX, minY, maxX, maxY) = motion
                cv2.rectangle(frame, (minX, minY), (maxX, maxY), (0, 0, 255), 2)
                # если приводы не заняты и прошло 0.5 сек с момента последнего наведения
                if not in_progress_hor and not in_progress_vert and time.time() - delay > 0.5:
                    # меняем флаги занятости и записываем координаты для наведения
                    in_progress_hor = True
                    in_progress_vert = True
                    last_captured = [minX + (maxX - minX) / 2, minY + (maxY - minY) / 2]
        # если режим наведения включен, осуществляем наведение
        if motion_focus:
            aim_motion()

        # обновляем фоновую модель
        # и увеличиваем число кадров
        md.update(gray)
        total += 1

        # устанавливаем кадр на вывод
        with lock:
            outputFrame = frame.copy()


def generate_image():
    global outputFrame, lock
    # цикл трансляции видеопотока
    while True:
        # ожидание получения lock
        with lock:
            # проверка на выводимый кадр
            if outputFrame is None:
                continue
            # кодирование в JPEG
            (flag, encodedImage) = cv2.imencode(".jpg", outputFrame)
            # проверка на успешность кодирования
            if not flag:
                continue
        # преобразование в байтовый формат для доступа к изображению по руту
        yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' +
               bytearray(encodedImage) + b'\r\n')


# рут трансляции
@app.route("/video_feed")
def video_feed():
    # возвращает запрос с изображением в байтовом формате
    # с соответствующим типом
    return Response(generate_image(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")


# рут получения углов поворота приводов
@app.route("/angle_feed", methods=['POST'])
def angle_feed():
    # возврат сериализованных параметров
    return jsonify({'horiz': sc.horiz_drive.read(), 'vert': sc.vert_drive.read()})


# руты поворота сервоприводов
@app.route('/rotate_left', methods=['POST'])
def rotate_left():
    sc.rotate_left()
    return ""


@app.route('/rotate_right', methods=['POST'])
def rotate_right():
    sc.rotate_right()
    return ""


@app.route('/rotate_up', methods=['POST'])
def rotate_up():
    sc.rotate_up()
    return ""


@app.route('/rotate_down', methods=['POST'])
def rotate_down():
    sc.rotate_down()
    return ""


@app.route('/rotate_default', methods=['POST'])
def rotate_default():
    sc.reset()
    return ""


# рут переключения режимов
@app.route('/toggle_mode', methods=['POST'])
def toggle_mode():
    global motion_focus
    motion_focus = not motion_focus
    message = motion_focus and "Motion lock" or "Manual mode"
    return jsonify(message)


if __name__ == '__main__':
    # создание потока для распознавания движения
    t = threading.Thread(target=frame_update, args=(32,))
    t.daemon = True
    t.start()
    # запуск приложения на локальном хосте
    app.run(host="0.0.0.0", port=8000, debug=True,
            threaded=True, use_reloader=False)

# сброс положения приводов
sc.reset()
# остановка трансляции
vs.stop()
