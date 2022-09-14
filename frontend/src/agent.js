import apiURLs from "./apiURLs"
import utils from "./utils"
const authMod = window.AppConfig.AUTH_MOD


export default {
    async isLoggedIn() {
        try {
            await utils.requestGET(apiURLs.user(), false)
        } catch (e) {
            switch(authMod){
                case window.AuthMod.OIDC:
                    return e.response?.status != 401
                default:{
                    window.console.error("Unkown error", e)
                }
            }
        }
        return true
    }
}
