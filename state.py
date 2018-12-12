# -*- coding: utf-8 -*-
import itertools
from numpy import floor, ceil
from copy import deepcopy

class Card:
  suits= ["♠ ","♡ ","♣ ", "♢ "]
  values= [str(i) for i in range(0,11)]

  def __init__(self, suit, value): #4 suits, 10 values
    self.suit= suit; self.value=value

  def __str__(self):
    return Card.suits[self.suit] + Card.values[self.value];

  def __eq__(self, other):
    if not isinstance(other, self.__class__): return False
    return self.suit==other.suit and self.value==other.value
  def __ne__(self,other):
    if isinstance(other, self.__class__): return True
    return self.suit!=other.suit or  self.value!=other.value

class state:
  def __init__(self, four_cards, reliquary):
    self.realm= [[None for _ in range(100)] for _ in range(3)] # Three rows of cards. Only even cells are represented!
    self.limits= (49,51) # leftmost card of the middle row, and rightmost card of the middle row
    self.realm[0][50], self.realm[1][49], self.realm[1][51], self.realm[2][50]= four_cards

    self.decks= [[Card(i,j) for j in range(1,11)] for i in range(4)] # One deck for each suit!

    self.reliquary= reliquary
    for c in self.reliquary+four_cards:
      self.decks[c.suit].remove(c)

    self.inventories= [[None for _ in range(4)] for _ in range(2)] # Player 0 is the current player
    self.phase= 0 # Phase 0 is choose action, phase 1 is revealing a card. If phase=1, then a revealed_card is None somewhere.

  def __str__(self):
    width= 30 # showing 30 columns
    center= (self.limits[0]+self.limits[1])/2.0
    left_side, right_side= int(floor(center-width/2.0)), int(ceil(center+width/2.0))

    result= "Reliquary: "+ " ".join([str(a) for a in self.reliquary])+"\n"
    result+= "Oponent cards: "+ " ".join([str(a) for a in self.inventories[1]])+"\n\n"

    for i in range(3):
      for j in range(left_side, right_side+1):
        if self.realm[i][j]==None: result+="   "
        else: result+= str(self.realm[i][j])
      result+="\n"
    result+="\n"
    result+= "Player cards: "+ " ".join([str(a) for a in self.inventories[0]])+"\n"
    result+= "phase: "+str(self.phase) +" limits: "+str(self.limits[0])+" "+ str(self.limits[1])+"\n"

    return result

  def who_won(self): # player 1 or player 0 won. None if it's still undecided.
    if any([None==c for c in self.inventories[0]]): return None
    my_values=[c.value for c in self.inventories[0]]
    if my_values[0]==my_values[1]==my_values[2]==my_values[3]: return 0

    if any([None==c for c in self.inventories[1]]): return None
    their_values=[c.value for c in self.inventories[1]]
    if their_values[0]==their_values[1]==their_values[2]==their_values[3]: return 1

    return None

  def revert_players(self):
    self.realm[0], self.realm[2]= self.realm[2], self.realm[0]
    self.inventories[0], self.inventories[1]= self.inventories[1], self.inventories[0]

  def next_empty_cells(self):
    moves=[]
    if self.realm[0][self.limits[0]-1]==None: moves.append((0,self.limits[0]-1));
    if self.realm[2][self.limits[0]-1]==None: moves.append((2,self.limits[0]-1));
    if self.realm[0][self.limits[0]-1]!=None and self.realm[2][self.limits[0]-1]!=None: moves.append((1,self.limits[0]-2))

    if self.realm[0][self.limits[1]+1]==None: moves.append((0,self.limits[1]+1));
    if self.realm[2][self.limits[1]+1]==None: moves.append((2,self.limits[1]+1));
    if self.realm[0][self.limits[1]+1]!=None and self.realm[2][self.limits[1]+1]!=None: moves.append((1,self.limits[1]+2))

    return moves

  def all_neighbours(self): # Lists all neighbours of a state. Depending on the action, the phase of a turn may change.
    neighbours=[]
    if self.who_won() in [0,1]: return neighbours

    # the decks, phase, and reliquary only change in the first two cases
    # the active player only changes after a card is drawn (case 0) or when no card is taken (case 2)

    # 0: If phase==1: select the next card from the deck and return
    if self.phase==1:
      for i in range(4):
        if self.decks[i] and self.reliquary[i]==None:
          for c in self.decks[i]:
            s2=deepcopy(self)
            s2.decks[i].remove(c); s2.reliquary[i]=c; s2.phase=0;
            s2.revert_players()
            neighbours.append(s2)
        return neighbours

    # 1: Try picking up a card from the reliquary
    for suit in range(4):
      if self.reliquary[suit]==None: continue

      s2=deepcopy(self)
      c= s2.reliquary[suit]; s2.reliquary[suit]=None; s2.phase=1

      if s2.inventories[0][suit]==None:
        s2.inventories[0][suit]= c
        neighbours.append(s2)
        continue
      else: # you have two cards of the same suit in your hand. Drop one.
        for x,y in s2.next_empty_cells():
          s3=deepcopy(s2)
          s3.realm[x][y]=c
          if x==1 and y==s3.limits[0]-2: s3.limits[0]-=2
          elif x==1 and y==s3.limits[1]+2: s3.limits[1]+=2
          neighbours.append(s3)

          s3=deepcopy(s2)
          s3.realm[x][y]= s3.inventories[0][suit]
          s3.inventories[0][suit]= c
          if x==1 and y==s3.limits[0]-2: s3.limits[0]-=2
          elif x==1 and y==s3.limits[1]+2: s3.limits[1]+=2

          neighbours.append(s3)

    # 2: Plot something evil
    for i in range(self.limits[0], self.limits[1]+1): for l in [+1, -1]:
      s2=deepcopy(self);
      cards= [s2.realm[0][i-l], s2.realm[1][i], s2.realm[2][i+l]]
      s2.realm[0][i-l], s2.realm[1][i], s2.realm[2][i+l]= (0,1,2)
      if any([c==None for c in cards]): continue
      if cards[2].value not in [c.value for c in self.inventories[0]]: continue

      cards+= s2.inventories[0]; s2.inventories[0]=[None]*4
      # ugh, four nested loops...
      permutations=[[c1,c2,c3,c4,c5,c6,c7] for c1 in cards if c1.suit==0
                                           for c2 in cards if c2.suit==1 and c2 not in [c1]
                                           for c3 in cards if c3.suit==2 and c3 not in [c1,c2]
                                           for c4 in cards if c4.suit==3 and c4 not in [c1,c2,c3]
                                           for c5 in cards if c5 not in [c1,c2,c3,c4]
                                           for c6 in cards if c6 not in [c1,c2,c3,c4,c5]
                                           for c7 in cards if c7 not in [c1,c2,c3,c4,c5,c6]]

      for p in permutations:
        s3=deepcopy(s2)
        s3.inventories[0]=[p[0],p[1],p[2],p[3]]
        s3.realm(0).



    return neighbours









