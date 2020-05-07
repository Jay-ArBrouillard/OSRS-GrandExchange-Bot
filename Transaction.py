class Transaction:
    def __init__(self, id = -1, name = None, price = 0, quantity = 0, profit = 0, buyOfferStart = 0, buyOfferEnd = 0, sellOfferStart = 0, sellOfferEnd = 0, elapsedTime = 0):
        self.id = id
        self.name = name
        self.price = price
        self.quantity = quantity
        self.profit = profit
        self.buyOfferStart = buyOfferStart
        self.buyOfferEnd = buyOfferEnd
        self.sellOfferStart = sellOfferStart
        self.quantisellOfferEndty = sellOfferEnd
        self.elapsedTime = elapsedTime