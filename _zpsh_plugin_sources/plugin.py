# coding=utf-8
from __future__ import absolute_import, division, unicode_literals, print_function

import jencodings  # noqa
import mcapi
import time
import functools
from copy import copy
from utils import format_exception, get_center, get_dots, get_middle
from data import PluginData
from collections import namedtuple

from org.bukkit.event import EventPriority
from org.bukkit.event.player import PlayerJoinEvent, PlayerMoveEvent
from org.bukkit.event.block import BlockBreakEvent
from org.bukkit import Location, Color, Effect, Material, Sound, TreeType, Particle, FireworkEffect, DyeColor, Bukkit, SandstoneType, GameMode
from org.bukkit.inventory import ItemStack
from org.bukkit.material import Wool, Sandstone

from com.sk89q.worldguard.protection.regions import ProtectedCuboidRegion
from com.sk89q.worldguard.protection.flags import DefaultFlag, StateFlag

db = PluginData()


class EventListener(PythonListener):
    plugin = None

    def __init__(self, *args, **kwargs):
        super(EventListener, self).__init__(*args, **kwargs)
        self.players_coords = {}

    def cancel_move(self, e, player, location):
        if player.name in self.players_coords:
            world, x, y, z = self.players_coords[player.name]
            block_location = Location(world, x + 0.5, y, z + 0.5, location.yaw, location.pitch)
            player.teleport(block_location)
        else:
            e.setCancelled(True)

    @PythonEventHandler(PlayerJoinEvent, EventPriority.NORMAL)
    def on_player_join(self, event):
        event.getPlayer().sendMessage('§bДобро пожаловать на сервер ЗПШ!')

    @PythonEventHandler(BlockBreakEvent, EventPriority.NORMAL)
    def on_block_break(self, event):
        block = event.getBlock()
        if block.type != Material.REDSTONE_LAMP_OFF and block.type != Material.REDSTONE_LAMP_ON:
            return

        print(block.x, block.y, block.z)
        for test_id, test in db.data['tests'].iteritems():
            for room_id, room in enumerate(test['rooms']):
                for output in room['outputs']:
                    if block.x == output[0] and block.y == output[1] and block.z == output[2]:
                        event.setCancelled(True)

                        if room['test_in_progress']:
                            continue

                        event.getPlayer().sendMessage('§bЗапускаю тесты...')
                        break
                else:
                    continue
                break

            else:
                continue
            break
        else:
            return

        player = event.getPlayer()

        with db.session() as data:
            data['tests'][test_id]['rooms'][room_id]['test_in_progress'] = True

        def _test():
            for check in test['tests']:
                for check_value, inp in zip(check['inputs'], room['inputs']):
                    inp_block = Location(player.world, inp[0], inp[1], inp[2]).getBlock()

                    def _update_block():
                        if check_value == 1:
                            inp_block.setType(Material.REDSTONE_BLOCK, True)
                        else:
                            inp_block.setType(Material.AIR, True)

                    Bukkit.getScheduler().callSyncMethod(self.plugin, _update_block).get()

                time.sleep(test['latency'])

                for output_value, _output in zip(check['outputs'], room['outputs']):
                    out_block = Location(player.world, _output[0], _output[1], _output[2]).getBlock()
                    output_real_value = int(out_block.type == Material.REDSTONE_LAMP_ON)

                    if output_value != output_real_value:
                        event.getPlayer().sendMessage('§4Тесты не прошли!')
                        break
                else:
                    continue

                break
            else:
                event.getPlayer().sendMessage('§bТесты прошли!')

                first, second = room['door']
                x = Location(player.world, first[0], first[1], first[2])
                y = Location(player.world, second[0], second[1], second[2])
                mcapi.fill(Material.AIR, x, y)

            with db.session() as _data:
                _data['tests'][test_id]['rooms'][room_id]['test_in_progress'] = False

            for inp in room['inputs']:
                inp_block = Location(player.world, inp[0], inp[1], inp[2]).getBlock()
                inp_block.setType(Material.AIR)

        Bukkit.getScheduler().runTaskAsynchronously(self.plugin, _test)

    @PythonEventHandler(PlayerMoveEvent, EventPriority.NORMAL)
    def move_event(self, e):
        player = e.getPlayer()
        name = player.getName()

        if player.hasPermission('zpsh.line_cross'):
            return

        player_location = player.getLocation()
        block_location = copy(player_location)

        for _ in range(5):
            block_location.y -= 1

            block = block_location.block
            if block.type == Material.WOOL and block.data == 14:
                player.sendMessage('§bНе пересекай §4§lКРАСНУЮ ЛИНИЮ!§c§b {}'.format(player.getName()))
                self.cancel_move(e, player, player_location)
                break

            if block.type == Material.WOOL and block.data != 0:
                if block.data == 15:
                    player.setAllowFlight(True)
                    player.setFlying(True)
                    player.getInventory().clear()
                    break

                player_color = db.data['players'].get(name, {}).get('color', None)
                if not player_color:
                    player.sendMessage('§bУ тебя нет цвета! Попроси Пуфита выдать тебе цвет!')
                    self.cancel_move(e, player, player_location)
                    break

                if block.data != player_color:
                    player.sendMessage('§bТвой цвет §{}{}§с§b! Пересекать можно только шерсть своего цвета'.format(
                        ZPSHPlugin.COLOR_FORMAT_CODE[player_color],
                        ZPSHPlugin.COLOR_NAME_RU[player_color],
                    ))
                    self.cancel_move(e, player, player_location)
                    break

        self.players_coords[name] = (
            player_location.world,
            int(player_location.x),
            int(player_location.y),
            int(player_location.z)
        )


Command = namedtuple('Command', ['name', 'permission', 'args_count'])


def command(name, permission=None, args_count=None):
    def _decorator(func):
        def _wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        _wrapper.command_meta = Command(name, permission, args_count)

        return _wrapper

    return _decorator


class ZPSHPlugin(PythonPlugin):
    LISTENERS = (
        EventListener,
    )

    COLOR_NAME_RU = {
        1: 'ОРАНЖЕВЫЙ',
        2: 'ПУРПУРНЫЙ',
        3: 'ГОЛУБОЙ',
        4: 'ЖЕЛТЫЙ',
        5: 'ЛАЙМОВЫЙ',
        6: 'РОЗОВЫЙ',
        7: 'СЕРЫЙ',
        8: 'СВЕТЛО-СЕРЫЙ',
        9: 'БИРЮЗОВЫЙ',
        10: 'ФИОЛЕТОВЫЙ',
        11: 'СИНИЙ',
        12: 'КОРИЧНЕВЫЙ',
        13: 'ЗЕЛЕНЫЙ',
    }

    COLOR_TO_DYE_COLOR = {
        1: DyeColor.ORANGE,
        2: DyeColor.MAGENTA,
        3: DyeColor.LIGHT_BLUE,
        4: DyeColor.YELLOW,
        5: DyeColor.LIME,
        6: DyeColor.PINK,
        7: DyeColor.GRAY,
        8: DyeColor.SILVER,
        9: DyeColor.CYAN,
        10: DyeColor.PURPLE,
        11: DyeColor.BLUE,
        12: DyeColor.BROWN,
        13: DyeColor.GREEN,
    }

    COLOR_FORMAT_CODE = {
        1: 6,
        2: 5,
        3: 'b',
        4: 'e',
        5: 'a',
        6: 'd',
        7: 8,
        8: 7,
        9: 3,
        10: 5,
        11: 1,
        12: 4,
        13: 2
    }

    def __init__(self, *args, **kwargs):
        super(ZPSHPlugin, self).__init__(*args, **kwargs)
        self.listeners = {}
        self.command_handlers = {}

    def register_listeners(self):
        pm = self.getServer().getPluginManager()

        for listener_class in self.LISTENERS:
            listener = listener_class()
            listener.plugin = self
            self.listeners[listener_class.__name__] = listener
            pm.registerEvents(listener, self)

    def onEnable(self):
        self.register_listeners()
        print("ZPSH plugin enabled")

    def onDisable(self):
        db.dump()
        print("ZPSH plugin disabled")

    def update_handlers(self):
        for m in dir(self):
            if m == 'dataFile':  # write-only, lol wtf
                continue

            if hasattr(getattr(self, m), 'command_meta'):
                method = getattr(self, m)
                self.command_handlers[method.command_meta.name] = method

    def onCommand(self, sender, cmd, label, args):
        if not self.command_handlers:  # not in __init__ due to some other jython magic
            self.update_handlers()

        handler = self.command_handlers.get(cmd.getName())

        if not handler:
            return False

        if handler.command_meta.permission and not sender.hasPermission(handler.command_meta.permission):
            sender.sendMessage('§4У тебя нет прав!')
            return True

        if handler.command_meta.args_count is not None and len(args) != handler.command_meta.args_count:
            return False

        return handler(sender, args)

    @command('py', permission='py.execute')
    def py(self, sender, args):
        if not args:
            return False

        try:
            exec(' '.join(args), globals())
        except Exception as e:
            sender.sendMessage(format_exception(e, with_traceback=True))
        return True

    @command('pyeval', permission='py.execute')
    def pyeval(self, sender, args):
        if not args:
            return False

        try:
            result = eval(' '.join(args), globals())
        except Exception as e:
            sender.sendMessage(format_exception(e, with_traceback=True))
        else:
            sender.sendMessage(repr(result))

        return True

    @command('register_player', permission='zpsh.register_players', args_count=2)
    def register_player(self, sender, args):
        player_name, player_id = args
        player_id = int(player_id)

        if player_id < 1 or player_id > 13:
            return False

        target = sender.getServer().getPlayerExact(player_name)

        with db.session() as data:
            data['players'][player_name] = {
                'color': player_id
            }

        target.getInventory().addItem(ItemStack(Material.WOOL, 1, player_id))
        target.sendMessage('§bТеперь твой цвет §{}{}§с§b! Обязательно запомни его'.format(
            self.COLOR_FORMAT_CODE[player_id],
            self.COLOR_NAME_RU[player_id],
        ))
        sender.sendMessage('§bDone')

        return True
 
    @command('remove_player', permission='zpsh.register_players', args_count=1)
    def remove_player(self, sender, args):
        player_name = args[0]

        with db.session() as data:
            data['players'].pop(player_name, None)

        sender.sendMessage('§bDone')
        return True

    @command('test_async', permission='zpsh.test_admin')
    def test_async(self, sender, args):
        def _test_function():
            import jencodings  # noqa
            time.sleep(5)
            print('lol')
            mcapi.set_block(Material.GOLD_BLOCK, sender.getLocation())
            time.sleep(10)
            print('kek')
            mcapi.set_block(Material.GOLD_BLOCK, sender.getLocation())

        Bukkit.getScheduler().runTaskAsynchronously(self, _test_function)

    @command('test_add', permission='zpsh.test_admin')
    def test_add(self, sender, args):
        test_id = args[0]
        inputs_count, outputs_count = db.data['tests'][test_id]['inputs_count'], db.data['tests'][test_id]['outputs_count']
        if len(args) != inputs_count + outputs_count + 1:
            return False

        test = {
            'inputs': list(map(int, args[1:inputs_count + 1])),
            'outputs': list(map(int, args[inputs_count + 1:]))
        }

        with db.session() as data:
            data['tests'][test_id]['tests'].append(test)

        return True

    @command('test_remove', permission='zpsh.test_admin', args_count=2)
    def test_remove(self, sender, args):
        test_id = args[0]
        index = int(args[1])

        with db.session() as data:
            data['tests'][test_id]['tests'].pop(index)

        return True

    @command('test_list', permission='zpsh.test_admin', args_count=1)
    def test_list(self, sender, args):
        for test in db.data['tests'][args[0]]['tests']:
            inputs = ' '.join(map(str, (test['inputs'])))
            outputs = ' '.join(map(str, (test['outputs'])))

            sender.sendMessage('§bInputs: §e{} §bOutputs: §4{}'.format(inputs, outputs))
        return True

    @command('test_latency', permission='zpsh.test_admin', args_count=2)
    def test_latency(self, sender, args):
        test_id = args[0]
        latency = float(args[1])

        with db.session() as data:
            data['tests'][test_id]['latency'] = latency

        return True

    @command('test_reload', permission='zpsh.test_admin', args_count=2)
    def test_reload(self, sender, args):
        test_id = args[0]
        room_id = int(args[1])

        with db.session() as data:
            data['tests'][test_id]['rooms'][room_id]['test_in_progress'] = False

        return True

    @command('create_test', permission='zpsh.test_admin', args_count=6)
    def create_test(self, sender, args):
        world_guard = self.getServer().getPluginManager().getPlugin('WorldGuard')

        test_id, players_count, x_size, y_size, inputs_count, outputs_count = args
        players_count, x_size, y_size, inputs_count, outputs_count = int(players_count), int(x_size), int(y_size), int(inputs_count), int(outputs_count)
        location = sender.getLocation()

        total_y_size = (x_size + 2) * players_count + players_count - 2
        total_x_size = y_size + 1

        location.y -= 1

        x, y, z = int(location.x), int(location.y), int(location.z)

        mcapi.fill(
            Material.AIR,
            Location(location.world, x, y - 1, z),
            Location(location.world, x + total_x_size, y + 5, z + total_y_size)
        )

        mcapi.fill(
            Material.SANDSTONE,
            Location(location.world, x + total_x_size + 1, y - 1, z),
            Location(location.world, x + total_x_size + 1, y + 5, z + total_y_size),
            data=Sandstone(SandstoneType.SMOOTH)
        )

        rooms = []
        for i in range(players_count):
            sub_test = {}
            offset = i * (x_size + 3)

            region_name = 'test_{}_{}'.format(test_id, i + 1)
            region = ProtectedCuboidRegion(
                region_name,
                mcapi.convert_to_bv(Location(location.world, x, y, z + offset)),
                mcapi.convert_to_bv(Location(location.world, x + y_size + 1, y + 5, z + x_size + 1 + offset)),
            )

            region_build_name = '{}_build'.format(region_name)
            region_build = ProtectedCuboidRegion(
                region_build_name,
                mcapi.convert_to_bv(Location(location.world, x + 1, y, z + offset + 1)),
                mcapi.convert_to_bv(Location(location.world, x + y_size, y + 4, z + x_size + offset)),
            )

            container = world_guard.getRegionContainer()
            regions = container.get(location.world)

            region.setFlag(DefaultFlag.GAME_MODE, GameMode.CREATIVE)
            region.setPriority(2)
            regions.addRegion(region)

            region_build.setFlag(DefaultFlag.BUILD, StateFlag.State.ALLOW)
            region_build.setPriority(3)
            regions.addRegion(region_build)

            mcapi.fill(
                Material.WOOL,
                Location(location.world, x, y, z + offset),
                Location(location.world, x + y_size + 1, y, z + offset),
                data=Wool(DyeColor.RED),
            )

            mcapi.fill(
                Material.WOOL,
                Location(location.world, x, y, z + offset),
                Location(location.world, x, y, z + x_size + 1 + offset),
                data=Wool(DyeColor.RED),
            )

            mcapi.fill(
                Material.WOOL,
                Location(location.world, x + y_size + 1, y, z + offset),
                Location(location.world, x + y_size + 1, y, z + x_size + 1 + offset),
                data=Wool(DyeColor.RED),
            )

            mcapi.fill(
                Material.WOOL,
                Location(location.world, x, y, z + x_size + 1 + offset),
                Location(location.world, x + y_size + 1, y, z + x_size + 1 + offset),
                data=Wool(DyeColor.RED),
            )

            if i != players_count - 1:
                mcapi.fill(
                    Material.WOOL,
                    Location(location.world, x, y, z + x_size + 2 + offset),
                    Location(location.world, x + y_size + 1, y, z + x_size + 2 + offset),
                    data=Wool(DyeColor.RED),
                )

                mcapi.fill(
                    Material.SANDSTONE,
                    Location(location.world, x, y + 1, z + x_size + 2 + offset),
                    Location(location.world, x + total_x_size + 1, y + 5, z + x_size + 2 + offset),
                    data=Sandstone(SandstoneType.SMOOTH)
                )

            mcapi.fill(
                Material.WOOL,
                Location(location.world, x + 1, y - 1, z + 1 + offset),
                Location(location.world, x + y_size, y, z + x_size + offset),
            )

            center_start, center_end = get_center(int(z + offset), int(z + offset + x_size + 1), 3)
            mcapi.fill(
                Material.WOOL,
                Location(location.world, x, y, center_start),
                Location(location.world, x, y, center_end),
                data=Wool(self.COLOR_TO_DYE_COLOR[i + 1]),
            )

            mcapi.fill(
                Material.WOOL,
                Location(location.world, x + y_size + 1, y, center_start),
                Location(location.world, x + y_size + 1, y, center_end),
                data=Wool(self.COLOR_TO_DYE_COLOR[i + 1]),
            )

            mcapi.fill(
                Material.BARRIER,
                Location(location.world, x, y + 5, z + offset),
                Location(location.world, x + y_size + 1, y + 5, z + x_size + 1 + offset)
            )

            inputs = []
            input_dots_x = get_dots(x, x + y_size + 1, inputs_count)
            for dot_x in input_dots_x:
                mcapi.set_block(
                    Material.GOLD_BLOCK,
                    Location(location.world, dot_x, y, z + 1 + x_size + offset),
                )
                mcapi.set_block(
                    Material.WOOL,
                    Location(location.world, dot_x, y - 1, z + 1 + x_size + offset),
                    data=Wool(DyeColor.RED),
                )

                inputs.append((dot_x, int(y + 1), int(z + 1 + x_size + offset)))

            sub_test['inputs'] = inputs

            outputs = []
            output_dots_x = get_dots(x, x + y_size + 1, outputs_count)
            for dot_x in output_dots_x:
                mcapi.set_block(
                    Material.REDSTONE_LAMP_OFF,
                    Location(location.world, dot_x, y + 1, z + offset),
                )

                outputs.append((dot_x, int(y + 1), int(z + offset)))

            sub_test['outputs'] = outputs

            door_start, door_end = get_center(z + offset, z + offset + x_size + 1, 3)
            mcapi.fill(
                Material.WOOL,
                Location(location.world, x + y_size + 2, y, door_start),
                Location(location.world, x + y_size + 2, y, door_end),
                data=Wool(DyeColor.BLACK),
            )

            sub_test['door'] = [
                (int(x + y_size + 2), int(y + 1), door_start),
                (int(x + y_size + 2), int(y + 3), door_end),
            ]

            sub_test['test_in_progress'] = False
            rooms.append(sub_test)

        with db.session() as data:
            data['tests'][test_id] = {
                'rooms': rooms,
                'test_id': test_id,
                'latency': 1,
                'tests': [],
                'inputs_count': inputs_count,
                'outputs_count': outputs_count,
            }

        return True
