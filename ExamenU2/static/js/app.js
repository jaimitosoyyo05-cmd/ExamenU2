const speedSlider =
    document.getElementById("speedSlider");

const sliderValue =
    document.getElementById("sliderValue");

const rpmActual =
    document.getElementById("rpmActual");

const setpointDisplay =
    document.getElementById("setpointDisplay");

const pwmValue =
    document.getElementById("pwmValue");

const errorValue =
    document.getElementById("errorValue");

const rpmBar =
    document.getElementById("rpmBar");

const startBtn =
    document.getElementById("startBtn");

const stopBtn =
    document.getElementById("stopBtn");

const connection =
    document.getElementById("connection");

const connectionText =
    document.getElementById("connectionText");


// ================================
// ACTUALIZAR PALANCA
// ================================

function actualizarSlider() {

    const valor =
        Number(speedSlider.value);

    sliderValue.textContent =
        valor;

    const porcentaje =
        valor;

    speedSlider.style.background =
        `linear-gradient(
            90deg,
            #4c8dff 0%,
            #4c8dff ${porcentaje}%,
            rgba(255,255,255,0.09) ${porcentaje}%,
            rgba(255,255,255,0.09) 100%
        )`;
}


// ================================
// MOVER PALANCA
// ================================

speedSlider.addEventListener(
    "input",
    actualizarSlider
);


// ================================
// APLICAR VELOCIDAD
// ================================

startBtn.addEventListener(
    "click",
    async () => {

        const rpm =
            Number(
                speedSlider.value
            );

        try {

            const respuesta =
                await fetch(
                    "/api/set_speed",
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body:
                            JSON.stringify({
                                rpm: rpm
                            })
                    }
                );


            if (
                respuesta.status === 401
            ) {

                window.location.href =
                    "/login";

                return;
            }


            const data =
                await respuesta.json();


            if (data.ok) {

                setpointDisplay.textContent =
                    rpm.toFixed(0);

                mostrarConectado();

            } else {

                mostrarDesconectado();
            }

        }

        catch (error) {

            console.error(
                error
            );

            mostrarDesconectado();
        }
    }
);


// ================================
// DETENER MOTOR
// ================================

stopBtn.addEventListener(
    "click",
    async () => {

        try {

            const respuesta =
                await fetch(
                    "/api/stop",
                    {
                        method: "POST"
                    }
                );


            if (
                respuesta.status === 401
            ) {

                window.location.href =
                    "/login";

                return;
            }


            const data =
                await respuesta.json();


            if (data.ok) {

                speedSlider.value =
                    0;

                sliderValue.textContent =
                    0;

                setpointDisplay.textContent =
                    0;

                actualizarSlider();

                mostrarConectado();

            } else {

                mostrarDesconectado();
            }

        }

        catch (error) {

            console.error(
                error
            );

            mostrarDesconectado();
        }
    }
);


// ================================
// LEER DATOS DEL MOTOR
// ================================

async function leerMotor() {

    try {

        const respuesta =
            await fetch(
                "/api/motor"
            );


        if (
            respuesta.status === 401
        ) {

            window.location.href =
                "/login";

            return;
        }


        const data =
            await respuesta.json();


        if (!data.ok) {

            mostrarDesconectado();

            return;
        }


        mostrarConectado();


        // RPM

        rpmActual.textContent =
            data.rpm.toFixed(1);


        // SETPOINT

        setpointDisplay.textContent =
            data.setpoint.toFixed(0);


        // PWM

        pwmValue.textContent =
            data.pwm.toFixed(1);


        // ERROR

        errorValue.textContent =
            data.error.toFixed(1);


        // BARRA RPM 0 - 100

        let porcentaje =
            data.rpm;


        if (porcentaje > 100) {

            porcentaje = 100;
        }


        if (porcentaje < 0) {

            porcentaje = 0;
        }


        rpmBar.style.width =
            porcentaje + "%";

    }

    catch (error) {

        console.error(
            error
        );

        mostrarDesconectado();
    }
}


// ================================
// CONECTADO
// ================================

function mostrarConectado() {

    connection.classList.remove(
        "offline"
    );

    connectionText.textContent =
        "Arduino conectado";
}


// ================================
// DESCONECTADO
// ================================

function mostrarDesconectado() {

    connection.classList.add(
        "offline"
    );

    connectionText.textContent =
        "Sin conexión";
}


// ================================
// INICIO
// ================================

actualizarSlider();

leerMotor();


// Actualizar datos cada 500 ms

setInterval(
    leerMotor,
    500
);