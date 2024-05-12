class Player:
    def __init__(self, name, chips=1000, is_dqn=False):
        self.name = name
        self.hand = []
        self.chips = chips
        self.in_game = True
        self.current_bet = 0
        self.total_bet = 0
        self.total_profit = 0
        self.is_dqn = is_dqn
