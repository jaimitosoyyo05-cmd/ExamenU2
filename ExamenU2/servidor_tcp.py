#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import signal
import time
import threading
import serial


# =========================
# CONFIGURACION TCP
# =========================

HOST = "0.0.0.0"
PORT = 5001


# =========================
# CONFIGURACION ARDUINO
# =========================

SERIAL_PORT = "/dev/ttyACM0"
BAUD = 115200


_running = True

_lock = threading.Lock()


# =========================
# CERRAR SERVIDOR
# =========================

def handle_sig(*_):

    global _running

    _running = False


# =========================
# ABRIR PUERTO SERIAL
# =========================

def open_serial():

    ser = serial.Serial(
        SERIAL_PORT,
        BAUD,
        timeout=2
    )

    print(
        "[SERIAL] Abriendo puerto..."
    )

    time.sleep(2)


    ser.reset_input_buffer()

    ser.reset_output_buffer()


    print(
        f"[SERIAL] Arduino conectado "
        f"en {SERIAL_PORT} @ {BAUD}"
    )


    return ser


# =========================
# ENVIAR COMANDO AL ARDUINO
# =========================

def send_to_arduino(
    ser,
    comando
):

    ser.write(
        (
            comando.strip()
            + "\n"
        ).encode("utf-8")
    )

    ser.flush()


    respuesta = (
        ser.readline()
        .decode(
            "utf-8",
            errors="ignore"
        )
        .strip()
    )


    if respuesta:

        return respuesta


    return "ERR sin respuesta del Arduino"


# =========================
# SERVIDOR
# =========================

def main():

    global _running


    signal.signal(
        signal.SIGINT,
        handle_sig
    )


    signal.signal(
        signal.SIGTERM,
        handle_sig
    )


    # =========================
    # CONECTAR ARDUINO
    # =========================

    try:

        ser = open_serial()

    except Exception as e:

        print(
            f"[ERROR SERIAL] {e}"
        )

        return


    # =========================
    # CREAR SERVIDOR TCP
    # =========================

    with socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    ) as servidor:


        servidor.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1
        )


        servidor.bind(
            (
                HOST,
                PORT
            )
        )


        servidor.listen(
            5
        )


        servidor.settimeout(
            0.5
        )


        print(
            f"[TCP] Servidor iniciado"
        )

        print(
            f"[TCP] Escuchando en "
            f"{HOST}:{PORT}"
        )


        # =========================
        # BUCLE PRINCIPAL
        # =========================

        while _running:

            try:

                conexion, direccion = (
                    servidor.accept()
                )

            except socket.timeout:

                continue


            with conexion:

                conexion.settimeout(
                    2
                )


                datos = b""


                try:

                    while True:

                        parte = conexion.recv(
                            1024
                        )


                        if not parte:

                            break


                        datos += parte


                        if b"\n" in datos:

                            break


                except socket.timeout:

                    pass


                comando = (
                    datos.decode(
                        "utf-8",
                        errors="ignore"
                    )
                    .strip()
                )


                # =========================
                # COMANDO VACIO
                # =========================

                if not comando:

                    conexion.sendall(
                        b"ERR comando vacio\n"
                    )

                    continue


                print(
                    f"[WEB] {comando}"
                )


                # =========================
                # ARDUINO
                # =========================

                try:

                    with _lock:

                        respuesta = (
                            send_to_arduino(
                                ser,
                                comando
                            )
                        )


                    print(
                        f"[ARDUINO] "
                        f"{respuesta}"
                    )


                    conexion.sendall(
                        (
                            respuesta
                            + "\n"
                        ).encode(
                            "utf-8"
                        )
                    )


                except Exception as e:

                    error = (
                        f"ERR {e}"
                    )


                    print(
                        error
                    )


                    conexion.sendall(
                        (
                            error
                            + "\n"
                        ).encode(
                            "utf-8"
                        )
                    )


    # =========================
    # CERRAR SERIAL
    # =========================

    try:

        ser.close()

    except Exception:

        pass


    print(
        "Servidor cerrado."
    )


# =========================
# INICIO
# =========================

if __name__ == "__main__":

    main()