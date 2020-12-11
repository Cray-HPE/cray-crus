
@Library('dst-shared@master') _

dockerBuildPipeline {
        repository = "cray"
        imagePrefix = "cray"
        app = "crus"
        name = "crus"
        description = "Compute Rolling Upgrade Service"
        useEntryPointForTest = "false"
        product = "csm"
        receiveEvent = ["MUNGE"]
}
