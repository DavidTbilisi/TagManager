# PowerShell script to batch tag files in C:\Users\David\Documents using tm.exe
# Uses filename (without extension) as the tag

$tm = Resolve-Path ".venv\Scripts\tm.exe"
$docs = Get-ChildItem -Path "C:\Users\David\Documents" -File

# Heuristic function to guess a one-word tag from the title
function Get-TopicTag($title) {
    $t = $title.ToLower()
    if ($t -match 'math|algebra|geometry|sudoku|logic|gre') { return 'math' }
    elseif ($t -match 'psychology|psycho|habit|memory|trauma|score|internal family systems') { return 'psychology' }
    elseif ($t -match 'security|hacking|cissp|ccna|comptia|cookies|privilege|linux') { return 'security' }
    elseif ($t -match 'language|chinese|chineasy|english|russian|logic') { return 'language' }
    elseif ($t -match 'productivity|system|systems|design|algorithm|architecture|project') { return 'productivity' }
    elseif ($t -match 'ruby|python|programmer|coding|code|powershell') { return 'programming' }
    elseif ($t -match 'finance|accounting|economics|business') { return 'finance' }
    elseif ($t -match 'bible|religion|spiritual|faith') { return 'spirituality' }
    elseif ($t -match 'test|quiz|flashcard|anki|practice|exam') { return 'study' }
    elseif ($t -match 'manual|guide|introduction|course|cheat|reference') { return 'guide' }
    else { return 'misc' }
}

foreach ($file in $docs) {
    $title = [System.IO.Path]::GetFileNameWithoutExtension($file.Name)
    $tag = Get-TopicTag $title
    # Remove all existing tags
    $existingTags = & $tm "path" $file.FullName | Select-String -Pattern '^\s*- ' | ForEach-Object { $_.ToString().Trim() -replace '^- ', '' }
    $title = [System.IO.Path]::GetFileNameWithoutExtension($file.Name)
    # Remove tags that match or are similar to the title (case-insensitive, ignore spaces and punctuation)
    $normalizedTitle = ($title -replace '[^a-zA-Z0-9]', '').ToLower()
    $tagsToRemove = @()
    foreach ($oldTag in $existingTags) {
        $normalizedTag = ($oldTag -replace '[^a-zA-Z0-9]', '').ToLower()
        if ($normalizedTag -eq $normalizedTitle) {
            $tagsToRemove += $oldTag
        }
    }
    if ($tagsToRemove.Count -gt 0) {
        Write-Host "Removing book-title-like tags from $($file.FullName): $($tagsToRemove -join ', ')"
        foreach ($removeTag in $tagsToRemove) {
            & $tm "remove" $file.FullName "--tags" $removeTag
        }
    }
    Write-Host "Tagging $($file.FullName) with tag '$tag'..."
    & $tm "add" $file.FullName "--tags" $tag
}
Write-Host "Batch tagging complete."
