const byte ENCODER_A = 2;
const byte ENCODER_B = 3;

const byte IN1 = 7;
const byte IN2 = 8;
const byte ENA = 9;

volatile long pulsos = 0;

// Pulsos por vuelta del encoder
const float PPR = 695.0;

// Velocidad
float setpoint = 0.0;
float rpm = 0.0;

// PID
float Kp = 0.8;
float Ki = 0.4;
float Kd = 0.02;

float error = 0.0;
float errorAnterior = 0.0;
float integral = 0.0;
float pwm = 0.0;

// Tiempo de muestreo
const unsigned long Ts = 100;
unsigned long tiempoAnterior = 0;


// ================================
// INTERRUPCION DEL ENCODER
// ================================

void encoderISR() {

  if (digitalRead(ENCODER_B)) {
    pulsos++;
  } else {
    pulsos--;
  }
}


// ================================
// SETUP
// ================================

void setup() {

  Serial.begin(115200);

  pinMode(ENCODER_A, INPUT_PULLUP);
  pinMode(ENCODER_B, INPUT_PULLUP);

  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(ENA, OUTPUT);

  attachInterrupt(
    digitalPinToInterrupt(ENCODER_A),
    encoderISR,
    RISING
  );

  // Sentido del motor
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);

  // Motor detenido al iniciar
  analogWrite(ENA, 0);

  tiempoAnterior = millis();

  Serial.println("OK MOTOR PID LISTO");
}


// ================================
// LOOP
// ================================

void loop() {

  leerComandos();

  unsigned long ahora = millis();

  if (ahora - tiempoAnterior >= Ts) {

    calcularRPM();

    controlarPID();

    tiempoAnterior = ahora;
  }
}


// ================================
// CALCULAR RPM
// ================================

void calcularRPM() {

  noInterrupts();

  long pulsosMedidos = pulsos;

  pulsos = 0;

  interrupts();

  float vueltas =
    pulsosMedidos / PPR;

  rpm =
    vueltas *
    (60000.0 / Ts);

  // Solo nos interesa la magnitud
  if (rpm < 0) {
    rpm = -rpm;
  }
}


// ================================
// CONTROL PID
// ================================

void controlarPID() {

  // Si el setpoint es 0
  // apagamos el motor

  if (setpoint <= 0) {

    pwm = 0;

    error = 0;

    integral = 0;

    errorAnterior = 0;

    analogWrite(
      ENA,
      0
    );

    return;
  }


  float dt =
    Ts / 1000.0;


  // ERROR

  error =
    setpoint - rpm;


  // INTEGRAL

  integral +=
    error * dt;


  // Limitar integral

  integral =
    constrain(
      integral,
      -100,
      100
    );


  // DERIVADA

  float derivada =
    (error - errorAnterior)
    / dt;


  // PID

  float salida =
    Kp * error
    +
    Ki * integral
    +
    Kd * derivada;


  // Modificar PWM

  pwm += salida;


  // Limitar PWM

  pwm =
    constrain(
      pwm,
      0,
      255
    );


  // Aplicar al L298N

  analogWrite(
    ENA,
    (int)pwm
  );


  errorAnterior =
    error;
}


// ================================
// COMANDOS DESDE RASPBERRY
// ================================

void leerComandos() {

  if (!Serial.available()) {
    return;
  }


  String comando =
    Serial.readStringUntil('\n');


  comando.trim();


  // ==============================
  // SET VELOCIDAD
  // ==============================

  if (
    comando.startsWith("SET ")
  ) {

    setpoint =
      comando.substring(4)
      .toFloat();


    // Limite 0 - 100 RPM

    setpoint =
      constrain(
        setpoint,
        0,
        100
      );


    Serial.print(
      "OK SET="
    );

    Serial.println(
      setpoint,
      1
    );
  }


  // ==============================
  // DETENER MOTOR
  // ==============================

  else if (
    comando == "STOP"
  ) {

    setpoint = 0;

    pwm = 0;

    error = 0;

    integral = 0;

    errorAnterior = 0;


    analogWrite(
      ENA,
      0
    );


    Serial.println(
      "OK STOP"
    );
  }


  // ==============================
  // LEER DATOS
  // ==============================

  else if (
    comando == "READ"
  ) {

    Serial.print(
      "OK RPM="
    );

    Serial.print(
      rpm,
      1
    );


    Serial.print(
      " SET="
    );

    Serial.print(
      setpoint,
      1
    );


    Serial.print(
      " PWM="
    );

    Serial.print(
      (pwm / 255.0) * 100.0,
      1
    );


    Serial.print(
      " ERROR="
    );

    Serial.println(
      setpoint - rpm,
      1
    );
  }


  // ==============================
  // COMANDO INCORRECTO
  // ==============================

  else {

    Serial.println(
      "ERR comando desconocido"
    );
  }
}