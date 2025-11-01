import wx
_ = wx.GetTranslation
#I'm sure this is very non-standard. Fake translation function so translated keys can be tagged without immediately translating them.
__ = lambda x: x