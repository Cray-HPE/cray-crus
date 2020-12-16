
@Library('dst-shared@release/shasta-1.4') _

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
