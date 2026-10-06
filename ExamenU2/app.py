#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    jsonify,
    send_file
)

import socket
import os
from datetime import datetime
from openpyxl import Workbook


# =========================
# CONFIGURACION
# =========================

APP_USER = "vboxuser"
APP_PASSWORD = "1234"

SECRET_KEY = "MOTOR_PID_WEB"

TCP_HOST = "127.0.0.1"
TCP_PORT = 5001


# =========================
# FLASK
# =========================

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/static"
)

app.secret_key = SECRET_KEY


# =========================
# HISTORIAL DE DATOS
# =========================

historial = []


# =========================
# LOGIN
# =========================

def is_logged_in():
    return session.get("logged_in") is True


# =========================
# COMUNICACION TCP
# =========================

def send_cmd(comando):

    with socket.create_connection(
        (TCP_HOST, TCP_PORT),
        timeout=3
    ) as s:

        s.sendall(
            (comando.strip() + "\n").encode("utf-8")
        )

        datos = b""

        while b"\n" not in datos:

            parte = s.recv(1024)

            if not parte:
                break

            datos += parte

        return datos.decode(
            "utf-8",
            errors="ignore"
        ).strip()


# =========================
# LOGIN
# =========================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        usuario = request.form.get(
            "username",
            ""
        )

        password = request.form.get(
            "password",
            ""
        )

        if (
            usuario == APP_USER
            and password == APP_PASSWORD
        ):

            session["logged_in"] = True

            return redirect(
                url_for("index")
            )

        return render_template(
            "login.html",
            error="Usuario o contraseña incorrectos"
        )

    return render_template(
        "login.html",
        error=None
    )


# =========================
# LOGOUT
# =========================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )


# =========================
# PAGINA PRINCIPAL
# =========================

@app.route("/")
def index():

    if not is_logged_in():

        return redirect(
            url_for("login")
        )

    return render_template(
        "index.html"
    )


# =========================
# CAMBIAR VELOCIDAD
# =========================

@app.post("/api/set_speed")
def set_speed():

    if not is_logged_in():

        return jsonify({
            "ok": False,
            "error": "No autorizado"
        }), 401

    try:

        datos = request.get_json(
            silent=True
        ) or {}

        rpm = float(
            datos.get("rpm", 0)
        )

        # Limite minimo
        if rpm < 0:
            rpm = 0

        # Limite maximo del proyecto
        if rpm > 100:
            rpm = 100

        comando = f"SET {rpm:.1f}"

        respuesta = send_cmd(
            comando
        )

        return jsonify({
            "ok": respuesta.startswith("OK"),
            "rpm": rpm,
            "respuesta": respuesta
        })

    except Exception as e:

        return jsonify({
            "ok": False,
            "error": str(e)
        })


# =========================
# DETENER MOTOR
# =========================

@app.post("/api/stop")
def stop_motor():

    if not is_logged_in():

        return jsonify({
            "ok": False,
            "error": "No autorizado"
        }), 401

    try:

        respuesta = send_cmd(
            "STOP"
        )

        return jsonify({
            "ok": respuesta.startswith("OK"),
            "respuesta": respuesta
        })

    except Exception as e:

        return jsonify({
            "ok": False,
            "error": str(e)
        })


# =========================
# LEER MOTOR
# =========================

@app.get("/api/motor")
def get_motor():

    if not is_logged_in():

        return jsonify({
            "ok": False,
            "error": "No autorizado"
        }), 401

    try:

        respuesta = send_cmd(
            "READ"
        )

        if not respuesta.startswith("OK"):

            return jsonify({
                "ok": False,
                "error": respuesta
            })

        # Respuesta esperada:
        #
        # OK RPM=50.2 SET=60.0 PWM=55.3 ERROR=9.8

        partes = respuesta.split()

        valores = {}

        for parte in partes[1:]:

            if "=" in parte:

                clave, valor = parte.split(
                    "=",
                    1
                )

                valores[clave] = float(
                    valor
                )


        rpm = valores.get(
            "RPM",
            0
        )

        setpoint = valores.get(
            "SET",
            0
        )

        pwm = valores.get(
            "PWM",
            0
        )

        error = valores.get(
            "ERROR",
            0
        )


        # =========================
        # GUARDAR EN HISTORIAL
        # =========================

        ahora = datetime.now()

        historial.append({

            "fecha":
                ahora.strftime(
                    "%d/%m/%Y"
                ),

            "hora":
                ahora.strftime(
                    "%H:%M:%S.%f"
                )[:-3],

            "setpoint":
                setpoint,

            "rpm":
                rpm,

            "error":
                error,

            "pwm":
                pwm
        })


        # Evita guardar datos infinitamente
        # en la memoria de la Raspberry

        if len(historial) > 20000:

            historial.pop(0)


        return jsonify({

            "ok": True,

            "rpm": rpm,

            "setpoint": setpoint,

            "pwm": pwm,

            "error": error
        })


    except Exception as e:

        return jsonify({
            "ok": False,
            "error": str(e)
        })


# =========================
# EXPORTAR EXCEL
# =========================

@app.get("/api/exportar")
def exportar():

    if not is_logged_in():

        return redirect(
            url_for("login")
        )

    try:

        wb = Workbook()

        ws = wb.active

        ws.title = "Control PID"


        # ENCABEZADOS

        ws.append([
            "Fecha",
            "Hora",
            "Setpoint (RPM)",
            "RPM Real",
            "Error (RPM)",
            "PWM (%)"
        ])


        # DATOS

        for dato in historial:

            ws.append([
                dato["fecha"],
                dato["hora"],
                dato["setpoint"],
                dato["rpm"],
                dato["error"],
                dato["pwm"]
            ])


        # ANCHO DE COLUMNAS

        ws.column_dimensions["A"].width = 15
        ws.column_dimensions["B"].width = 16
        ws.column_dimensions["C"].width = 18
        ws.column_dimensions["D"].width = 15
        ws.column_dimensions["E"].width = 15
        ws.column_dimensions["F"].width = 15


        # CONGELAR ENCABEZADO

        ws.freeze_panes = "A2"


        # NOMBRE DEL ARCHIVO

        nombre = (
            "datos_PID_JGA370_"
            + datetime.now().strftime(
                "%Y%m%d_%H%M%S"
            )
            + ".xlsx"
        )


        ruta = os.path.join(
            "/tmp",
            nombre
        )


        wb.save(
            ruta
        )


        return send_file(
            ruta,
            as_attachment=True,
            download_name=nombre
        )


    except Exception as e:

        return jsonify({
            "ok": False,
            "error": str(e)
        })


# =========================
# PING
# =========================

@app.get("/api/ping")
def ping():

    if not is_logged_in():

        return jsonify({
            "ok": False
        }), 401

    return jsonify({
        "ok": True
    })


# =========================
# INICIAR FLASK
# =========================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )