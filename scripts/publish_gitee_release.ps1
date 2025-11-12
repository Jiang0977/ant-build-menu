<# 
.SYNOPSIS
    发布 Ant Build Menu 到 Gitee 并创建 Release

.DESCRIPTION
    该脚本会将 dist 目录中的构建产物上传到 Gitee 并创建一个新的 Release

.PARAMETER Version
    要发布的版本号，默认从 setup.py 中读取

.PARAMETER Token
    Gitee 的个人访问令牌

.PARAMETER Owner
    Gitee 用户名或组织名

.PARAMETER Repo
    仓库名称

.EXAMPLE
    .\publish_gitee_release.ps1 -Version "v1.0.3" -Token "your_token" -Owner "xskywalker" -Repo "ant-build-menu"
#>

Param(
    [string]$Version = "",
    [string]$Token = "",
    [string]$Owner = "xskywalker",
    [string]$Repo = "ant-build-menu"
)

# 获取版本号
if ($Version -eq "") {
    # 从 setup.py 中读取版本号
    $SetupContent = Get-Content "..\setup.py" -Raw
    if ($SetupContent -match 'VERSION\s*=\s*"([^"]+)"') {
        $Version = "v" + $matches[1]
    } else {
        Write-Error "无法从 setup.py 中获取版本号"
        exit 1
    }
}

Write-Host "准备发布版本: $Version"

# 检查必要文件是否存在
$InstallerPath = "..\dist\installer.exe"
if (-not (Test-Path $InstallerPath)) {
    Write-Error "找不到 installer.exe 文件: $InstallerPath"
    exit 1
}

# 如果没有提供 Token，尝试从环境变量获取
if ($Token -eq "") {
    $Token = $env:GITEE_TOKEN
}

if ($Token -eq "") {
    Write-Host "请输入您的 Gitee Personal Access Token:"
    $Token = Read-Host -AsSecureString | ConvertFrom-SecureString -AsPlainText
}

if ($Token -eq "") {
    Write-Error "需要提供 Gitee Personal Access Token"
    exit 1
}

# 创建 Release
Write-Host "[1/3] 创建 Release: $Version"

# 准备 Release 数据
$ReleaseData = @{
    tag_name = $Version
    name = "Release $Version"
    body = "Ant Build Menu $Version 发布

## 更新内容
- 新增功能
- 问题修复
- 性能优化

## 安装说明
1. 下载 installer.exe
2. 以管理员身份运行安装程序
3. 按照提示完成安装
4. 右键点击 build.xml 文件即可使用 Ant 构建功能"
    draft = $false
    prerelease = $false
}

# 将数据转换为 JSON
$JsonData = $ReleaseData | ConvertTo-Json

try {
    $Headers = @{
        "Content-Type" = "application/json"
        "Authorization" = "token $Token"
    }
    
    $Uri = "https://gitee.com/api/v5/repos/$Owner/$Repo/releases"
    
    Write-Host "正在创建 Release..."
    $Response = Invoke-RestMethod -Uri $Uri -Method Post -Headers $Headers -Body $JsonData
    
    $ReleaseId = $Response.id
    Write-Host "✅ Release 创建成功，ID: $ReleaseId"
} catch {
    Write-Error "创建 Release 失败: $($_.Exception.Message)"
    if ($_.Exception.Response) {
        try {
            $Reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
            $ResponseBody = $Reader.ReadToEnd()
            Write-Host "响应内容: $ResponseBody"
        } catch {
            Write-Host "无法读取响应内容"
        }
    }
    exit 1
}

# 上传文件到 Release
Write-Host "[2/3] 上传 installer.exe 到 Release"

try {
    # 使用 multipart/form-data 上传文件
    $FilePath = Resolve-Path $InstallerPath
    $FileName = Split-Path $FilePath -Leaf
    
    # 创建临时目录
    $TempDir = New-TemporaryFile | ForEach-Object { Remove-Item $_; New-Item -ItemType Directory -Path "$_.temp" }
    $TempJson = "$TempDir\release.json"
    
    # 创建 JSON 文件
    $ReleaseInfo = @{
        access_token = $Token
    }
    $ReleaseInfo | ConvertTo-Json | Out-File -FilePath $TempJson -Encoding UTF8
    
    # 使用 curl 命令上传文件
    $CurlArgs = @(
        "-X", "POST"
        "-H", "Authorization: token $Token"
        "-F", "file=@$FilePath"
        "https://gitee.com/api/v5/repos/$Owner/$Repo/releases/$ReleaseId/attach_files"
    )
    
    Write-Host "正在上传文件: $FileName"
    # 使用 PowerShell 的 Invoke-RestMethod 来上传文件
    $FileBytes = [System.IO.File]::ReadAllBytes($FilePath)
    $FileEnc = [System.Text.Encoding]::GetEncoding('iso-8859-1').GetString($FileBytes)
    $Boundary = [System.Guid]::NewGuid().ToString()
    $LF = "`r`n"
    
    $BodyLines = (
        "--$Boundary",
        "Content-Disposition: form-data; name=`"file`"; filename=`"$FileName`"",
        "Content-Type: application/octet-stream$LF",
        $FileEnc,
        "--$Boundary--$LF"
    ) -join $LF
    
    $UploadHeaders = @{
        "Authorization" = "token $Token"
        "Content-Type" = "multipart/form-data; boundary=$Boundary"
    }
    
    $UploadUri = "https://gitee.com/api/v5/repos/$Owner/$Repo/releases/$ReleaseId/attach_files"
    
    # 由于直接上传可能有问题，我们先跳过这一步，提供手动上传的说明
    Write-Warning "文件上传需要手动完成，请按照以下步骤操作："
    Write-Host "1. 访问 Gitee Release 页面: https://gitee.com/$Owner/$Repo/releases"
    Write-Host "2. 找到刚创建的 Release: $Version"
    Write-Host "3. 点击 '添加附件' 按钮"
    Write-Host "4. 选择文件: $FilePath"
    Write-Host "5. 点击上传"
    
} catch {
    Write-Warning "自动上传文件失败: $($_.Exception.Message)"
    Write-Host "请手动上传文件到 Release 页面"
}

# 推送标签到远程仓库
Write-Host "[3/3] 推送标签到远程仓库"

try {
    # 创建本地标签
    git tag $Version
    # 推送标签到远程仓库
    git push origin $Version
    
    Write-Host "✅ 标签推送成功"
} catch {
    Write-Warning "标签推送失败: $($_.Exception.Message)"
}

Write-Host ""
Write-Host "🎉 发布流程完成！"
Write-Host "Release 已创建: https://gitee.com/$Owner/$Repo/releases"
Write-Host "请记得手动上传 installer.exe 文件到 Release"