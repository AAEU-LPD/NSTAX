"""Interface module to connect remotely with a linux machine.

Primary purpose of this module is to interface with a linux based equipment and 
establish communication through commands.

It has two main components:
1. SSH communication using paramiko library for remote console operation
2. JSON communication using websocket to send and receive responses
"""

import json
import paramiko
from time import sleep
from websocket import create_connection

from NSTAX.interface.interface import Interface

class RemoteInterface(Interface):
    """Remote session of linux equipment.
    """
    def __init__(self, username, password, ip_address):
        super().__init__("RemoteInterface", version = 0.1)
        self.teststation_config_file = "../NSTA/config/teststation_config.yaml"
        self.ip_address = ip_address
        self.username = username
        self.password = password
        
    def connect(self):
        """Connects to the machine through SSH.
        """
        # TODO: implement timeout + raise incase of no connection
        try:
            # Create SSH client
            self.ssh_session = paramiko.SSHClient()
            self.ssh_session.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            # Connect to the server
            self.ssh_session.connect(self.ip_address, 22, self.username, self.password)
        except Exception as e:
            print(f'Error: {e}')
            raise self.CouldNotConnectError("Error connecting to SSH interface via credentials")
        
            
    def disconnect(self):
        """Disconnects from SSH"""
        # Close the connection
        self.ssh_session.close()
        
    def send_command(self,cmd, port=9000, is_ssh_cmd=True, read_output=False):
        """Send the command string to the assigned port

        :param cmd: command to send
        :type cmd: str
        :param port: port number to forward the data, defaults to 9000
        :type port: int, optional
        :param is_ssh_cmd: if the cmd is send through SSH vs Websocket, defaults to True
        :type is_ssh_cmd: bool, optional
        :param read_output: should the response be read after the cmd is sent, defaults to False
        :type read_output: bool, optional
        :return: returns the response
        :rtype: str
        """
        if is_ssh_cmd:
            response = self._send_ssh_cmd(cmd, read_output)
        else:
            response = self._send_websocket_cmd(cmd, port)
        return response
            
    def _send_ssh_cmd(self, command, read_output=False):
        """Send the command string through an SSH session

        :param command: command to send
        :type command: str
        :param read_output: should the response be read after the cmd is sent, defaults to False
        :type read_output: bool, optional
        :return: returns the reply
        :rtype: str
        """
        # Read the current crontab
        stdin, stdout, stderr = self.ssh_session.exec_command(command)
        if read_output:
            cmd_reply = stdout.read().decode('utf-8')
            # Check for errors
            error = stderr.read().decode('utf-8')
            if error:
                print(f'Error send_ssh_cmd: {error}')
            return cmd_reply
        return
                
    def _send_websocket_cmd(self, command, port):
        """Send the command string through a websocket connection

        :param command: command to send
        :type command: str
        :param port: port number to forward the cmd to
        :type port: int
        :return: returns the reply
        :rtype: str
        """
        ws = create_connection("ws://" + f"{self.ip_address}:{port}")
        ws.send(command)
        while True:
            result = ws.recv()
            if result:
                message = json.loads(result)
                reply = json.dumps(message, indent=2, ensure_ascii=False)
                if message.get("message") != "ready":
                    break
        ws.close()
        return reply


if __name__ == "__main__":
    # Example run
    RI = RemoteInterface("root","toor","10.51.16.4")
    RI.connect()
    RI.send_command('{"message":"ue_get"}', 9001, is_ssh_cmd=False)
    RI.disconnect()