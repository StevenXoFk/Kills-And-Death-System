from endstone.plugin import Plugin
from endstone.event import event_handler, PlayerDeathEvent, PlayerJoinEvent
from endstone import ColorFormat, Player
from endstone.command import Command, CommandSender
from pathlib import Path
import json

class MyPlugin(Plugin):
    api_version = "0.10"

    commands = {
        "stats": {
            "description": "View a player's statistics",
            "usage": ["/stats [player: str]"],
            "permissions": ["my_plugin.command.stats"]
        }
    }

    permissions = {
        "my_plugin.command.stats": {
            "description": "Allow users to use the /stats command.",
            "default": True,
        }
    }
    def on_enable(self):
        self.logger.info(f'{ColorFormat.GREEN}El Plugin se cargo correctamente')
        self.players_folder = self.data_folder / "players"
        self.players_folder.mkdir(parents=True, exist_ok=True)

        self.register_events(self)
    def on_disable(self):
        self.logger.info(f'${ColorFormat.RED}El plugin se cerro correctamente')

    def on_command(self, sender: CommandSender, command: Command, args: list[str]):
        if (command.name == "stats"):
            if not isinstance(sender, Player):
                sender.send_error_message(ColorFormat.RED + "This command is only used on players")
                return False

            player_name = sender.name if not args else args[0]

            online_player = self.server.get_player(player_name)
            sender.send_message(
                f'{ColorFormat.YELLOW}{online_player.name} Stats{ColorFormat.RESET}\n\n'
                f'{ColorFormat.YELLOW}Kills: {ColorFormat.RESET}{self.get_stat(online_player.name, "kills")}\n'
                f'{ColorFormat.YELLOW}Deaths: {ColorFormat.RESET}{self.get_stat(online_player.name, "deaths")}'
            )
            return True

    @event_handler
    def on_player_death(self, event: PlayerDeathEvent):
        player = event.player
        damage_source = event.damage_source

        self._add_stat(player.name, "deaths", 1)

        if damage_source is not None:
            as_player = damage_source.damaging_actor

            if isinstance(as_player, Player):
                self._add_stat(as_player.name, "kills", 1)

                self.server.broadcast_message(
                    f'{ColorFormat.MATERIAL_REDSTONE}{player.name} '
                    f'[{ColorFormat.WHITE}{self.get_stat(player.name, "kills")}{ColorFormat.MATERIAL_REDSTONE}]'
                    f'{ColorFormat.YELLOW} was slain by '
                    f'{ColorFormat.MATERIAL_REDSTONE}{as_player.name} '
                    f'[{ColorFormat.WHITE}{self.get_stat(as_player.name, "kills")}{ColorFormat.MATERIAL_REDSTONE}]'
                )
                return

        self.server.broadcast_message(event.death_message)

    @event_handler
    def on_player_join(self, event: PlayerJoinEvent):
        player = event.player
        file_path = self.players_folder / f"{player.name}.json"

        if not file_path.exists():
            data = {
                "kills": 0,
                "deaths": 0
            }

            with file_path.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            self.logger.info(f"Stats de {player.name} creados")

    def _add_stat(self, player_name: str, stat: str, amount: int):
        file_path = self.players_folder / f"{player_name}.json"

        if not file_path.exists():
            data = {"kills": 0, "deaths": 0}
        else:
            with file_path.open("r", encoding="utf-8") as f:
                data = json.load(f)

        data[stat] = data.get(stat, 0) + amount

        with file_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def get_stat(self, player_name: str, stat: str, default=0):
        file_path = self.players_folder / f"{player_name}.json"

        if not file_path.exists():
            return default

        try:
            with file_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            return default

        return data.get(stat, default)