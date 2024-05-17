import tkinter as tk
from tkinter import filedialog
from network.client import Client  # Suponiendo que este es tu módulo para la comunicación de red


def open_audio_file_dialog():
    root = tk.Tk()
    root.withdraw()  # Oculta la ventana principal de tkinter
    file_path = filedialog.askopenfilename(
        title="Seleccionar archivo de audio",
        filetypes=(("Archivos de audio", "*.wav;*.mp3"), ("Todos los archivos", "*.*"))
    )
    return file_path


def main():
    # Obtener el archivo de audio si se seleccionó
    file_path = open_audio_file_dialog()

    print("Archivo de audio seleccionado:", file_path)

    # Inicializar el cliente con el host y el puerto del router
    router_host = "localhost"
    router_port = int(input("Puerto: "))  # Se pide al usuario ingresar el puerto
    client = Client(router_host, router_port)

    # Conectar al router
    client.connect()

    # Obtener entradas del usuario
    destination = input("Ingrese destino: ")
    message = input("Ingrese mensaje: ")

    # Enviar el mensaje, con o sin archivo adjunto
    if file_path:
        with open(file_path, 'rb') as f:
            filedata = f.read()
        client.send_message(destination, message, is_file=True, binary=filedata)
    else:
        client.send_message(destination, message)

    # Recibir respuesta si es necesario
    response = client.receive_message()
    if response:
        print("Respuesta recibida:", response)

    # Detener el cliente
    client.stop()


if __name__ == "__main__":
    main()
