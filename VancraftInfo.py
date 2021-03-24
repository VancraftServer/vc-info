#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import socket
import struct
import json
import time
import dns.resolver
# import csv
import os
# from matplotlib import pyplot as plt


def _unpack_varint(sock):
    data = 0
    for i in range(5):
        ordinal = sock.recv(1)

        if len(ordinal) == 0:
            break

        byte = ord(ordinal)
        data |= (byte & 0x7F) << 7 * i

        if not byte & 0x80:
            break

    return data


def _pack_varint(data):
    ordinal = b''

    while True:
        byte = data & 0x7F
        data >>= 7
        ordinal += struct.pack('B', byte | (0x80 if data > 0 else 0))

        if data == 0:
            break

    return ordinal


def _pack_data(data):
    if type(data) is str:
        data = data.encode('utf8')
        return _pack_varint(len(data)) + data
    elif type(data) is int:
        return struct.pack('H', data)
    elif type(data) is float:
        return struct.pack('Q', int(data))
    else:
        return data


def _send_data(connection, *args):
    data = b''

    for arg in args:
        data += _pack_data(arg)

    connection.send(_pack_varint(len(data)) + data)


def _read_fully(connection, extra_varint=False):
    packet_length = _unpack_varint(connection)
    packet_id = _unpack_varint(connection)
    byte = b''

    if extra_varint:

        if packet_id > packet_length:
            _unpack_varint(connection)

        extra_length = _unpack_varint(connection)

        while len(byte) < extra_length:
            byte += connection.recv(extra_length)

    else:
        byte = connection.recv(packet_length)

    return byte


def get_motd(timeout, host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as connection:
        connection.settimeout(timeout)
        connection.connect((host, port))

        _send_data(connection, b'\x00\x00', host, port, b'\x01')
        _send_data(connection, b'\x00')

        data = _read_fully(connection, extra_varint=True)

        _send_data(connection, b'\x01', time.time() * 1000)
        _read_fully(connection)

    response = json.loads(data.decode('utf8'))

    return response


def get_info():
    print('正在收集服务器信息...')
    dns_response = dns.resolver.resolve('_minecraft._tcp.mc.vancraft.cn', 'SRV')
    for i in dns_response.response.answer:
        for j in i.items:
            host = str(j.target).strip('.')
            port = j.port
    info_dict = get_motd(10, host, port)
    info_player_num = info_dict['players']['online']
    info_time = time.strftime('%y/%m/%d-%H:%M', time.localtime())
    # info_useful = {}
    print('成功获取到信息：{1}, {0}.'.format(str(info_player_num), info_time))
    print('正在将数据保存至文件...')
    # header = True
    # if os.path.exists('vc_info.csv'):
    #     header = False
    # csv_file = open('vc_info.csv', 'a+', newline='')
    # csv_writer = csv.DictWriter(csv_file, [
    #     '时间',
    #     '玩家数',
    # ])
    # if header:
    #     csv_writer.writeheader()
    # csv_writer.writerow({
    #     '时间': info_time,
    #     '玩家数': info_player_num,
    # })
    # csv_file.close()
    if not os.path.exists('vc_week_info.json'):
        with open('vc_week_info.json', 'w') as f:
            f.write('[]')
    with open('vc_week_info.json', 'r') as f:
        data = json.loads(f.read())
    with open('vc_week_info.json', 'w') as f:
        # date = time.strftime('%y/%m/%d', time.localtime())
        week = time.strftime('%y-%W', time.localtime())
        # print(type(data))
        if data[0]['week'] == week:
            data.append({
                'week': week,
                'time': info_time,
                'player_num': info_player_num
            })
        else:
            data = [{
                'week': week,
                'time': info_time,
                'player_num': info_player_num
            }]
        json.dump(data, f)
    if not os.path.exists('vc_day_info.json'):
        with open('vc_day_info.json', 'w') as f:
            f.write('[]')
    with open('vc_day_info.json', 'r') as f:
        data = json.loads(f.read())
    with open('vc_day_info.json', 'w') as f:
        date = time.strftime('%y/%m/%d', time.localtime())
        # week = time.strftime('%y-%W', time.localtime())
        # print(type(data))
        if data[0]['date'] == date:
            data.append({
                'date': date,
                'time': info_time,
                'player_num': info_player_num
            })
        else:
            data = [{
                'date': date,
                'time': info_time,
                'player_num': info_player_num
            }]
        json.dump(data, f)
    print('成功将数据保存至文件.')
    # print('开始绘制数据图表...')
    # csv_file = open('vc_info.csv', 'r')
    # csv_reader = csv.reader(csv_file)
    # used_time, used_player_num = [], []
    # i = 0
    # for j in csv_reader:
    #     if i == 0:
    #         i += 1
    #         continue
    #     used_time.append(j[0])
    #     used_player_num.append(j[1])
    # used_time, used_player_num = used_time[-10::], used_player_num[-10::]
    # fig = plt.figure(dpi=128, figsize=(10, 6))
    # plt.plot(used_time, used_player_num, c='red')
    # plt.title('Vancraft Player Data', fontsize=24)
    # plt.xlabel('Time', fontsize=16)
    # fig.autofmt_xdate()
    # plt.ylabel('Player(s)', fontsize=16)
    # plt.tick_params(axis='both', which='major', labelsize=16)
    # plt.savefig('vc_info_img.png', bbox_inches='tight')
    # csv_file.close()


def main():
    get_info()


if __name__ == '__main__':
    main()
