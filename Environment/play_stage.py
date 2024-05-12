import json
import random
from typing import List
from player import Player
from collections import namedtuple
from hand_check import evaluate_hand, map_suit, map_level

Card = namedtuple('Card', ['rank', 'suit'])

class TexasHoldem:
    def __init__(self, players: List[Player], small_blind, big_blind, history_file):

        # 玩家信息
        self.players = players
        self.num_players = len(players)
        self.init_player()

        # 牌局信息
        self.pot, self.small_blind, self.big_blind = 0, small_blind, big_blind
        self.community_cards, self.deck = [], self.create_deck()

        # 历史信息
        self.history_file = f"history/{history_file}.json"
        self.card_history, self.betting_history, self.log = {}, {}, {}
        self.pot_log = []

        # 游戏状态
        self.init_player()
        self.chips_history = {p.name: str(p.chips) for p in self.players}
        self.blinding()


    def create_deck(self):
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
        deck = [Card(rank, suit) for suit in suits for rank in ranks]
        random.shuffle(deck)
        return deck


    def init_player(self):
        for player in self.players:
            player.hand = []
            player.total_bet = 0
            player.in_game = True
            player.chips = 500 if player.chips == 0 else 500


    def blinding(self):
        self.players[0].chips -= self.small_blind
        self.players[0].total_bet = self.small_blind
        self.players[1].chips -= self.big_blind
        self.players[1].total_bet = self.big_blind
        self.betting_history["小盲"] = f"{self.players[0].name} 下注{self.small_blind}"
        self.betting_history["大盲"] = f"{self.players[1].name} 下注{self.big_blind}"


    def deal(self):
        hand_card = {}
        for player in self.players:
            if player.in_game:
                card1 = self.deck.pop()
                card2 = self.deck.pop()
                player.hand.extend([card1, card2])
                hand_card[player.name] = f"{map_suit(card1.suit)}{card1.rank}, {map_suit(card2.suit)}{card2.rank}"     
        self.card_history["手牌"] = hand_card


    def flop(self):
        cards = [self.deck.pop() for _ in range(3)]
        self.card_history["翻牌"] = [f"{map_suit(card.suit)}{card.rank}" for card in cards]
        self.community_cards.extend(cards)


    def turn_or_river(self):
        card = self.deck.pop()
        if len(self.community_cards) == 3:
            self.card_history["转牌"] = f"{map_suit(card.suit)}{card.rank}"
        else:
            self.card_history["河牌"] = f"{map_suit(card.suit)}{card.rank}"
        self.community_cards.append(card)

    def betting_round(self, name, is_preflop=False):
        start_player = 2 if is_preflop else 0
        current_bet = self.big_blind if is_preflop else 0
        min_raise = self.big_blind
        last_raiser = None
        done = False
        epoch = 1
        for p in self.players: p.current_bet = 0
        if is_preflop: self.players[0].current_bet, self.players[1].current_bet = self.small_blind, self.big_blind
        if len([p for p in self.players if p.in_game and p.chips > 0]) > 1:
            while not done:
                done = True
                temp_history = []
                for i in range(start_player, len(self.players) + start_player):
                    player = self.players[i % len(self.players)]
                    if player.in_game is False or player.chips == 0: continue
                    if player == last_raiser or len([p for p in self.players if p.in_game]) == 1: break
                    bet_amount = player.response(self.community_cards, current_bet, min_raise, self.players, self.big_blind)
                    if bet_amount == -1: 
                        player.in_game = False
                        temp_history.append(player.name + " 弃牌")
                    else:
                        player.current_bet += bet_amount
                        if bet_amount == player.chips: move = 'all in'
                        elif player.current_bet == current_bet: move = '跟注'
                        else: move = '加注'
                        temp_history.append(player.name + f" {move}至{player.current_bet}, 加注{bet_amount}, 与当前轮注差额为{player.current_bet - current_bet}")
                        player.total_bet += bet_amount
                        self.pot += bet_amount   
                        player.chips -= bet_amount
                        if player.current_bet - current_bet >= min_raise:
                            min_raise = player.current_bet - current_bet 
                        if player.current_bet > current_bet:
                            current_bet = player.current_bet
                            last_raiser = player
                            done = False
                if len(temp_history) != 0:
                    self.betting_history[f"{name}round {epoch}"] = temp_history[:]
                    epoch += 1
    
    def evaluate_winner_hands(self):
        winner_hands = []
        for player in self.players:
            if player.in_game:
                combined_cards = player.hand + self.community_cards
                hand_strength = evaluate_hand(combined_cards)
                winner_hands.append((player, hand_strength))
        self.card_history["牌力"] = {player.name: f"{map_level(x[0])}{x[1]}" for player, x in winner_hands}
        return winner_hands
    
    def judge_winner(self, winners):
        winner = []
        for player in winners:
            combined_cards = player.hand + self.community_cards
            hand_strength = evaluate_hand(combined_cards)
            if len(winner) == 0 or hand_strength > winner[0][1]:
                winner = [(player, hand_strength)]
            elif hand_strength == winner[0][1]:
                winner.append((player, hand_strength))
        return [p for p, _ in winner]

    def distribute_pot(self):
        winner_hands = self.evaluate_winner_hands()
        winners = sorted([p for p, _ in winner_hands], key=lambda x: x.total_bet)
        temp_winners = winners[:]
        pre_bet = 0
        winner_pot = [[[], 0] for _ in range(len(winners))]
        for i in range(len(winners)):
            winner = winners[i]
            winner_current_bet = winner.total_bet
            winner_pot[i][0].extend(temp_winners)
            temp_winners = temp_winners[1:]
            for player in self.players:
                if min(player.total_bet, winner_current_bet) > pre_bet:
                    winner_pot[i][1] += min(player.total_bet, winner_current_bet) - pre_bet
            pre_bet = winner_current_bet
        for winners, pot in winner_pot:
            if pot == 0: continue
            pot_winner = self.judge_winner(winners)
            logs = {"奖池": pot, "玩家": f"{[p.name for p in winners]}", "赢家": f"{[p.name for p in pot_winner]}"}
            for winner in pot_winner[:-1]:
                winner.chips += pot // len(pot_winner)
            pot_winner[-1].chips += pot // len(pot_winner) + pot % len(pot_winner)
            self.pot_log.append(logs)
        for player in self.players:
            if player.is_dqn:
                player.feedback(self.pot_log[0]['玩家'], self.pot_log[0]['赢家'], self.players, self.community_cards)
            change = player.chips - int(self.chips_history[player.name])
            player.total_profit += change
            self.log[player.name] = change
            self.chips_history[player.name] += f"->{player.chips}, total_profit: {player.total_profit}"

    def write_log(self):
        with open(self.history_file, "w") as f:
            f.write(json.dumps(self.betting_history, ensure_ascii=False, indent=4) + "\n")
            f.write(json.dumps(self.card_history, ensure_ascii=False, indent=4) + "\n")
            f.write(json.dumps(self.pot_log, ensure_ascii=False, indent=4) + "\n")
            f.write(json.dumps(self.chips_history, ensure_ascii=False, indent=4) + "\n")
             
    def process_game(self):
        self.deal()
        self.betting_round("Preflop", is_preflop=True)  # 前翻牌加注
        if len([p for p in self.players if p.in_game]) > 1:
            self.flop()
            self.betting_round("Flop")
        if len([p for p in self.players if p.in_game]) > 1:
            self.turn_or_river()  # 转牌
            self.betting_round("Turn")
        if len([p for p in self.players if p.in_game]) > 1:
            self.turn_or_river()  # 河牌
            self.betting_round("River")
        self.distribute_pot()
        self.write_log()