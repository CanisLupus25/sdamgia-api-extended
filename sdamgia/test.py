from sdamgia import SdamGIA
import pprint

sdamgia = SdamGIA(exam='oge')
pprint.pprint(sdamgia.get_problem_by_id('math', ['66']))