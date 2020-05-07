class GEItem:
    def __init__(self, id = -1, name = None, members = None, price = None, highAlch = None, buyLimit = None, noteable = None, tradeable_on_ge = None, stackable = None, timestamp = None):
        self.id = id
        self.name = name
        self.members = members
        self.price = price
        self.highAlch = highAlch
        self.buyLimit = buyLimit
        self.noteable = noteable
        self.tradeable_on_ge = tradeable_on_ge
        self.stackable = stackable
        self.timestamp = timestamp

    def __str__(self):
        return str(self.name) + " " + str(self.tradeable_on_ge)