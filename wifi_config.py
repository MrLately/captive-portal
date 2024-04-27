import network
import ujson
import socket
from time import sleep

ap = network.WLAN(network.AP_IF)
ap.active(False)

print("AP initialized and set to inactive.")

def load_credentials():
    try:
        with open('wifi_credentials.json', 'r') as file:
            creds = ujson.load(file)
        print("Credentials loaded successfully:", creds)
        return creds
    except Exception as e:
        print("Failed to load credentials:", str(e))
        return None

def save_credentials(creds):
    try:
        with open('wifi_credentials.json', 'w') as file:
            ujson.dump(creds, file)
        print("Credentials saved successfully.")
    except Exception as e:
        print("Failed to save credentials:", str(e))

def connect_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Attempting to connect to WiFi:", ssid)
        wlan.connect(ssid, password)
        timeout = 10
        while not wlan.isconnected() and timeout > 0:
            sleep(1)
            timeout -= 1
        if wlan.isconnected():
            print("Connected to WiFi. IP:", wlan.ifconfig()[0])
            return wlan.ifconfig()[0]
        else:
            print("Failed to connect to WiFi.")
            return None
    else:
        print("Already connected. IP:", wlan.ifconfig()[0])
        return wlan.ifconfig()[0]

def setup_ap():
    ap.config(essid='PiPico-Setup', password='setup1234')
    ap.active(True)
    print("AP setup with SSID: PiPico-Setup and Password: setup1234")
    
def serve_page():
    import socket, network
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(1)
    print("Server is listening...")

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    html_form = """HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n
    <!DOCTYPE html>
    <html>
    <head>
        <title>Setup WiFi</title>
    </head>
    <body>
        <h1>Setup WiFi</h1>
        <form action="/" method="get">
            SSID: <input type='text' name='ssid'><br>
            Password: <input type='password' name='password'><br>
            <input type='submit' value='Connect'>
        </form>
        <!-- Placeholder for displaying the IP address -->
        <div id="ip_address"></div>
        <script>
        // Keep the access point active as long as the setup page is open
        window.onbeforeunload = function() {{
            fetch('/keep_ap_active');
        }};
        </script>
    </body>
    </html>"""

    while True:
        cl, addr = s.accept()
        request = cl.recv(1024)
        request = str(request)
        print("Received request:", request)

        if '?ssid=' in request and '&password=' in request:
            ssid_start = request.find('?ssid=') + 6
            ssid_end = request.find('&', ssid_start)
            password_start = request.find('&password=') + 10
            password_end = request.find(' HTTP', password_start)
            ssid = request[ssid_start:ssid_end]
            password = request[password_start:password_end]

            creds = {'ssid': ssid, 'password': password}
            save_credentials(creds)
            ip_address = connect_wifi(ssid, password)
            if ip_address:
                response = f"""HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n
                <html><head></head>
                <body><h1>Connection Successful</h1>
                <p>IP Address: {ip_address}</p>
                <form action="/close_ap" method="get">
                <input type='submit' value='Continue'>
                </form>
                </body></html>"""
            else:
                response = """HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n
                <html><body><h1>Connection Failed</h1><p>Please try again.</p></body></html>"""
            cl.send(response.encode())
        elif '/keep_ap_active' in request:
            cl.send("HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nAP Active".encode())
        elif '/close_ap' in request:
            ap.active(False)  # Deactivate the access point
            response = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nAccess point closed."
            cl.send(response.encode())
        else:
            cl.send(html_form.encode())

        cl.close()


def main():
    creds = load_credentials()
    if not creds or not connect_wifi(creds['ssid'], creds['password']):
        setup_ap()
        serve_page()

if __name__ == '__main__':
    main()




