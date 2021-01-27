import * as storeModules from './modules/'
import * as getters from './getters'
import * as actions from './actions'

const modules = {
    app: {
        namespaced: true,
        ...storeModules.app,
    },
    task: {
        namespaced: true,
        ...storeModules.task,
    },
}


export {
    getters,
    actions,
    modules,
}