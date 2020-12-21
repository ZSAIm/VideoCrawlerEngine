
from helper.payload.flow import FlowPayload
from helper.payload.request import requester
from helper.payload import stack


@requester('function')
def stack_function(funcid, args, kwargs):
    func = stack.get(funcid)
    return func(*args, **kwargs)
