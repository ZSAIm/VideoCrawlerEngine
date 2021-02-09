function genModulesNamespaceStore(objs = [], fromStore = {}) {
    for (let obj of objs) {
        let getters = obj.getters || {};
        let actions = obj.actions || {};
        let mutations = obj.mutations || {};
        let state = obj.state || {};
        fromStore = {
            getters: {
                ...fromStore.getters,
                ...getters,
            },
            actions: {
                ...fromStore.actions,
                ...actions,
            },
            mutations: {
                ...fromStore.mutations,
                ...mutations,
            },
            state: {
                ...fromStore.state,
                ...state,
            }
        }

    }
    return fromStore
}


function capitalize(str) {
    return str.toLowerCase().replace(/( |^)[a-z]/g, (L) => L.toUpperCase())
}


function deepCopyJsonObject(obj) {
    return JSON.parse(JSON.stringify(obj))
}


export {
    genModulesNamespaceStore,
    capitalize,
    deepCopyJsonObject,
}