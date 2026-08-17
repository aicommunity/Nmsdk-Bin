# Лабораторные конфиги StandardFirmata

Сценарий: открыли `Project.ini` → увидели схему **Assembly** → собрали по BOM →
Upload / Connect / ApplyConfig → увидели результат в **Monitor**, инспекторе `Value` / `ValueIn`
или на светодиоде платы.

Hub-сэмплы 14–16 **не** входят в этот документ (не StandardFirmata).

## Общие шаги (один раз)

1. NeuroModeler → открыть `Bin/Configs/SpikeSamples/Hardware/<каталог>/Project.ini`.
2. На канвасе клик по узлу **Firmata**. Виджет: **Assembly** | **Pinout** | **Pins** | **Monitor** | **Board**.
3. Вкладка **Board**: `PortName` = `COM3`, `BoardProfile` = **1** (Arduino Mega 2560).
4. **Upload** bundled firmware `standard_firmata` (если плата ещё без StandardFirmata).
5. **Connect**. Дождаться `FirmataReady` / handshake.
6. Собрать схему по вкладке **Assembly** и BOM карточки (если нужны внешние детали).
7. DeviceIO: **ApplyConfig**, затем Continuous / Calculate. Результат — не Watch: вкладка
   **Monitor**, свойство `Value` / `ValueIn`, светодиод D13 / серво / мотор.

Без датчиков на столе проверяются только **03** и **17**.

Генерация: `python Scripts/generate_arduino_hardware_configs.py --port COM3 --board-profile 1`

![Arduino Mega 2560 Rev3](_shared/media/Arduino_MEGA2560.png)

*Arduino, [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/), [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Arduino_MEGA2560.png). Pinout PDF: [Mega A000067](_shared/media/A000067-full-pinout.pdf) / [Uno A000066](_shared/media/A000066-full-pinout.pdf) (Arduino, CC BY-SA 4.0).*


## Карточки конфигов

### 03-ArduinoFirmata — пульт пинов

- **BOM:** плата + USB.
- **Assembly:** setup не задан; смотрите **Pinout** / **Pins**.
- **Шаги:** Upload → Connect → Pins: D13 OUTPUT, WriteDigital 1.
- **Успех:** handshake, встроенный светодиод D13 реагирует с пульта Pins; Monitor показывает сэмплы.

### 17-DeviceIO-LED — встроенный светодиод

- **BOM:** плата + USB (датчики не нужны).
- **Assembly:** модуль `led` на D13.
- **Шаги:** Connect → ApplyConfig на `Led` → `Led.ValueIn` = 1.
- **Успех:** светодиод D13 горит при `ValueIn` ≥ 0.5, гаснет при 0.

### 18-DeviceIO-PotToPwmLed — потенциометр → PWM LED

- **BOM:** потенциометр, светодиод, резистор ~220 Ω, провода.
- **Assembly:** `potentiometer` A0 + `pwm_led` D9.
- **Шаги:** собрать как Analog In/Out → Connect → ApplyConfig → Continuous; крутить A0.
- **Успех:** `Pot.Value` 0..1, яркость LED на D9 следует за потенциометром.

### 08-ArduinoFirmata-AnalogLink — AnalogSamples → Adc

- **BOM:** потенциометр на A0.
- **Assembly:** нет DeviceIO; Firmata + Adc.
- **Успех:** `Adc.AdcValue` / `Firmata.AnalogSamples` меняются при вращении (A0 = Firmata pin 54).

### 09-HardwareSetup-SensorShield — только схема

- **BOM:** как 10+11 (pot A0, servo D9), но IO-узлов нет.
- **Assembly:** Sensor Shield + pot + servo.
- **Успех:** схема на вкладке Assembly; IO читайте в лабах 10/11.

### 10-DeviceIO-Potentiometer

- **BOM:** потенциометр A0.
- **Успех:** `Pot.Value` меняется 0..1 в инспекторе / Continuous.

### 11-DeviceIO-Servo

- **BOM:** сервопривод D9.
- **Успех:** `Servo.ValueIn` 0..1 поворачивает вал (0 → ~0°, 1 → ~180°).

### 12-MotorShield-R3

- **BOM:** Arduino Motor Shield R3 + 1–2 DC-мотора, внешнее питание шилда.
- **Успех:** короткий импульс `MotorA.ValueIn` крутит канал A. Не держите PWM > 0 долго без мотора/радиатора.
- Seeed: смените `HardwareSetupPath` на `../_shared/MotorShieldSeeedSetup.json`.

### 13-Sensors-To-Pulse — pot + кнопка

- **BOM:** потенциометр A0 + кнопка D2.
- **Успех:** `Pot.Value` и `Btn.Value` в инспекторе; Monitor Firmata. Watch добавлять не нужно.

## Источники

- Arduino docs: [docs.arduino.cc](https://docs.arduino.cc/) — **CC BY-SA 4.0**
  ([LICENSE](https://github.com/arduino/docs-content/blob/main/LICENSE.md)).
  Pinout: [UNO A000066](https://docs.arduino.cc/resources/pinouts/A000066-full-pinout.pdf),
  [Mega A000067](https://docs.arduino.cc/resources/pinouts/A000067-full-pinout.pdf).
- Analog In/Out: [AnalogInOutSerial](https://docs.arduino.cc/built-in-examples/analog/AnalogInOutSerial/).
- Firmata: [github.com/firmata/arduino](https://github.com/firmata/arduino),
  [API](https://firmata.github.io/arduino/html/index.html) — исходники LGPL-2.1, здесь только ссылки.
- Фото Mega: [Arduino MEGA2560.png](https://commons.wikimedia.org/wiki/File:Arduino_MEGA2560.png) — Arduino, CC BY-SA 4.0.
- Фото Uno: [Arduino Uno - R3.jpg](https://commons.wikimedia.org/wiki/File:Arduino_Uno_-_R3.jpg) — SparkFun Electronics, CC BY 2.0.
- Габаритные SVG Uno/Mega: [Wayne and Layne](https://www.wayneandlayne.com/blog/2010/12/19/nice-drawings-of-the-arduino-uno-and-mega-2560/) — public domain.
- Полная таблица файлов: `Libraries/Rdk-HardwareLib/Catalog/assets/ATTRIBUTION.md`.

Arduino — товарный знак Arduino SA; логотип как марка продукта не используется.
CC BY-SA share-alike относится к vendored-файлам в `assets/` / `_shared/media/`, не ко всему SDK.
