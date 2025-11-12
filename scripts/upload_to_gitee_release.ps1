<# 
.SYNOPSIS
    上传文件到 Gitee Release

.DESCRIPTION
    该脚本用于手动上传文件到已创建的 Gitee Release

.PARAMETER Owner
    Gitee 用户名或组织名

.PARAMETER Repo
    仓库名称

.PARAMETER ReleaseId
    Release ID

.PARAMETER Token
    Gitee 的个人访问令牌

.PARAMETER FilePath
    要上传的文件路径

.EXAMPLE
    .\upload_to_gitee_release.ps1 -Owner "xskywalker" -Repo "ant-build-menu" -ReleaseId 12345 -Token "your_token" -FilePath "..\dist\installer.exe"
#>

Param(
    [Parameter(Mandatory=$true)]
    [string]$Owner,
    
    [Parameter(Mandatory=$true)]
    [string]$Repo,
    
    [Parameter(Mandatory=$true)]
    [string]$ReleaseId,
    
    [Parameter(Mandatory=$true)]
    [string]$Token,
    
    [Parameter(Mandatory=$true)]
    [string]$FilePath
)

# 检查文件是否存在
if (-not (Test-Path $FilePath)) {
    Write-Error "文件不存在: $FilePath"
    exit 1
}

# 获取文件名
$FileName = Split-Path $FilePath -Leaf
Write-Host "准备上传文件: $FileName"

# 使用 curl 上传文件到 Gitee Release
try {
    Write-Host "正在上传文件到 Gitee Release..."
    
    # 使用 curl 命令上传文件
    $CurlCommand = "curl -X POST `"https://gitee.com/api/v5/repos/$Owner/$Repo/releases/$ReleaseId/attach_files`" " +
                   "-H `"Authorization: token $Token`" " +
                   "-F `"file=@$FilePath`""
    
    Write-Host "执行命令: $CurlCommand"
    Invoke-Expression $CurlCommand
    
    Write-Host "✅ 文件上传成功: $FileName"
} catch {
    Write-Error "文件上传失败: $($_.Exception.Message)"
    exit 1
}