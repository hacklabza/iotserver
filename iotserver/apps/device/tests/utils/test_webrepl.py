import pytest

from iotserver.apps.device.utils import webrepl


@pytest.mark.parametrize(
    ('remote', 'expected'),
    [
        ('device.local:config.json', ('device.local', 8266, 'config.json')),
        ('device.local:9000:config.json', ('device.local', 9000, 'config.json')),
        ('device.local:', ('device.local', 8266, '/')),
    ],
)
def test_parse_remote(remote, expected):
    assert webrepl.parse_remote(remote) == expected


def test_get_websocket(mocker):
    socket_instance = mocker.Mock()
    mocker.patch.object(webrepl.socket, 'socket', return_value=socket_instance)
    mocker.patch.object(
        webrepl.socket,
        'getaddrinfo',
        return_value=[(None, None, None, None, ('192.0.2.1', 8266))],
    )
    client_handshake = mocker.patch.object(webrepl, 'client_handshake')
    login = mocker.patch.object(webrepl, 'login')
    get_ver = mocker.patch.object(webrepl, 'get_ver', return_value=(1, 2, 3))
    web_socket = mocker.Mock()
    mocker.patch.object(webrepl, 'WebSocket', return_value=web_socket)

    result = webrepl.get_websocket('device.local', 8266, 'password')

    assert result == (socket_instance, web_socket)
    socket_instance.connect.assert_called_once_with(('192.0.2.1', 8266))
    client_handshake.assert_called_once_with(socket_instance)
    login.assert_called_once_with(web_socket, 'password')
    get_ver.assert_called_once_with(web_socket)
    web_socket.ioctl.assert_called_once_with(9, 2)
