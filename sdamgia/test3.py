import pprint

from sdamgia import SdamGIA

sdamgia = SdamGIA(exam='oge')
pprint.pprint(sdamgia.get_catalog('math'))