"use client"

import React, { useState, useEffect } from "react"
import {
  Search,
  Home,
  Folder,
  File,
  ChevronRight,
  Grid3x3,
  List,
  FileText,
  Image as ImageIcon,
  Archive,
  FileCode,
  MoreVertical,
  Loader2,
  AlertCircle,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card } from "@/components/ui/card"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Alert, AlertDescription } from "@/components/ui/alert"
import {
  listFolders,
  listFiles,
  handleFileManagerError,
  type Folder as FolderType,
  type File as FileType,
  type BreadcrumbItem,
} from "@/services/filemanager.api"

type ViewMode = "grid" | "hierarchy"

export function FileManager() {
  const [searchQuery, setSearchQuery] = useState("")
  const [currentFolderId, setCurrentFolderId] = useState<string | null>(null)
  const [breadcrumbs, setBreadcrumbs] = useState<BreadcrumbItem[]>([
    { id: null, name: "Главная" }
  ])
  const [viewMode, setViewMode] = useState<ViewMode>("grid")

  // API Data
  const [folders, setFolders] = useState<FolderType[]>([])
  const [files, setFiles] = useState<FileType[]>([])

  // Loading & Error states
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Fetch folders and files when currentFolderId changes
  useEffect(() => {
    fetchFolderContents()
  }, [currentFolderId])

  const fetchFolderContents = async () => {
    setLoading(true)
    setError(null)

    try {
      // Fetch folders and files in parallel
      const [foldersResponse, filesResponse] = await Promise.all([
        listFolders(currentFolderId),
        listFiles(currentFolderId)
      ])

      setFolders(foldersResponse.folders)
      setFiles(filesResponse.files)
    } catch (err) {
      const errorMessage = handleFileManagerError(err)
      setError(errorMessage)
      console.error("Error fetching folder contents:", err)
    } finally {
      setLoading(false)
    }
  }

  // Filter by search query
  const filteredFolders = searchQuery
    ? folders.filter(folder =>
        folder.name.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : folders

  const filteredFiles = searchQuery
    ? files.filter(file =>
        file.filename.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : files

  // Handle folder double click
  const handleFolderDoubleClick = (folder: FolderType) => {
    setCurrentFolderId(folder.id)
    setBreadcrumbs([...breadcrumbs, { id: folder.id, name: folder.name }])
  }

  // Handle breadcrumb click
  const handleBreadcrumbClick = (index: number) => {
    const newBreadcrumbs = breadcrumbs.slice(0, index + 1)
    setBreadcrumbs(newBreadcrumbs)
    setCurrentFolderId(newBreadcrumbs[newBreadcrumbs.length - 1].id)
  }

  // Navigate to home
  const handleHomeClick = () => {
    setCurrentFolderId(null)
    setBreadcrumbs([{ id: null, name: "Главная" }])
  }

  // Get file icon based on MIME type
  const getFileIcon = (mimeType?: string) => {
    if (!mimeType) return <File className="w-5 h-5 text-muted-foreground" />

    if (mimeType.startsWith("image/")) {
      return <ImageIcon className="w-5 h-5 text-green-500" />
    } else if (
      mimeType.includes("pdf") ||
      mimeType.includes("document") ||
      mimeType.includes("text")
    ) {
      return <FileText className="w-5 h-5 text-blue-500" />
    } else if (
      mimeType.includes("zip") ||
      mimeType.includes("compressed") ||
      mimeType.includes("archive")
    ) {
      return <Archive className="w-5 h-5 text-yellow-500" />
    } else if (
      mimeType.includes("javascript") ||
      mimeType.includes("json") ||
      mimeType.includes("html") ||
      mimeType.includes("css")
    ) {
      return <FileCode className="w-5 h-5 text-purple-500" />
    }

    return <File className="w-5 h-5 text-muted-foreground" />
  }

  // Format file size
  const formatFileSize = (bytes: number): string => {
    if (!bytes) return "0 B"
    const k = 1024
    const sizes = ["B", "KB", "MB", "GB"]
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`
  }

  // Format date
  const formatDate = (dateString: string): string => {
    const date = new Date(dateString)
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    })
  }

  // Build hierarchy tree for hierarchy view
  const buildHierarchyTree = (parentId: string | null = null, level: number = 0): React.ReactNode => {
    const childFolders = folders.filter(f => f.parentID === parentId)
    const childFiles = files.filter(f => f.folder_id === parentId)

    if (childFolders.length === 0 && childFiles.length === 0) return null

    return (
      <div className={level > 0 ? "ml-6 border-l border-border pl-4" : ""}>
        {/* Folders first */}
        {childFolders.map(folder => (
          <div key={folder.id} className="my-1">
            <div
              className="flex items-center gap-2 p-2 rounded-md hover:bg-muted cursor-pointer transition-colors"
              onDoubleClick={() => handleFolderDoubleClick(folder)}
            >
              <Folder className="w-4 h-4 text-primary flex-shrink-0" />
              <span className="text-sm font-medium">{folder.name}</span>
              <span className="text-xs text-muted-foreground ml-auto">
                {formatDate(folder.updated_at)}
              </span>
            </div>
            {buildHierarchyTree(folder.id, level + 1)}
          </div>
        ))}

        {/* Then files */}
        {childFiles.map(file => (
          <div
            key={file.id}
            className="flex items-center gap-2 p-2 rounded-md hover:bg-muted cursor-pointer transition-colors my-1"
          >
            {getFileIcon(file.file_type)}
            <span className="text-sm">{file.filename}</span>
            <span className="text-xs text-muted-foreground ml-auto">
              {formatFileSize(file.file_size)}
            </span>
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="flex h-full bg-background">
      {/* Main Content */}
      <main className="flex-1 flex flex-col h-full">
        {/* Header */}
        <header className="border-b border-border bg-card p-4">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={handleHomeClick}
                className="gap-2"
              >
                <Home className="w-4 h-4" />
                Главная
              </Button>
            </div>
            <div className="flex-1 relative max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
              <Input
                type="text"
                placeholder="Поиск файлов и папок..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10"
              />
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant={viewMode === "grid" ? "default" : "ghost"}
                size="icon"
                onClick={() => setViewMode("grid")}
                title="Сетка"
              >
                <Grid3x3 className="w-5 h-5" />
              </Button>
              <Button
                variant={viewMode === "hierarchy" ? "default" : "ghost"}
                size="icon"
                onClick={() => setViewMode("hierarchy")}
                title="Иерархия"
              >
                <List className="w-5 h-5" />
              </Button>
            </div>
          </div>
        </header>

        {/* Breadcrumbs */}
        <div className="border-b border-border bg-background px-6 py-3">
          <div className="flex items-center gap-2 text-sm">
            {breadcrumbs.map((breadcrumb, index) => (
              <React.Fragment key={index}>
                {index > 0 && <ChevronRight className="w-4 h-4 text-muted-foreground" />}
                <button
                  onClick={() => handleBreadcrumbClick(index)}
                  className={`hover:text-foreground transition-colors ${
                    index === breadcrumbs.length - 1
                      ? "text-foreground font-medium"
                      : "text-muted-foreground"
                  }`}
                >
                  {breadcrumb.name}
                </button>
              </React.Fragment>
            ))}
          </div>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-auto p-6">
          {/* Error State */}
          {error && (
            <Alert variant="destructive" className="mb-4">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Loading State */}
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="flex flex-col items-center gap-2">
                <Loader2 className="w-8 h-8 animate-spin text-primary" />
                <p className="text-sm text-muted-foreground">Загрузка...</p>
              </div>
            </div>
          ) : viewMode === "grid" ? (
            // Grid View
            <div className="space-y-8">
              {/* Folders Section */}
              {filteredFolders.length > 0 && (
                <div>
                  <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-4">
                    Папки ({filteredFolders.length})
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                    {filteredFolders.map((folder) => (
                      <Card
                        key={folder.id}
                        className="p-4 cursor-pointer hover:bg-muted/50 transition-colors group"
                        onDoubleClick={() => handleFolderDoubleClick(folder)}
                      >
                        <div className="flex items-start gap-3">
                          <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                            <Folder className="w-5 h-5 text-primary" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <h4 className="font-medium truncate">{folder.name}</h4>
                            <p className="text-sm text-muted-foreground mt-1">
                              {formatDate(folder.updated_at)}
                            </p>
                          </div>
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button
                                variant="ghost"
                                size="icon"
                                className="opacity-0 group-hover:opacity-100 transition-opacity"
                                onClick={(e) => e.stopPropagation()}
                              >
                                <MoreVertical className="w-4 h-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem onClick={() => handleFolderDoubleClick(folder)}>
                                Открыть
                              </DropdownMenuItem>
                              <DropdownMenuItem disabled>Переименовать</DropdownMenuItem>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem className="text-destructive" disabled>
                                Удалить
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </div>
                      </Card>
                    ))}
                  </div>
                </div>
              )}

              {/* Files Section */}
              {filteredFiles.length > 0 && (
                <div>
                  <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-4">
                    Файлы ({filteredFiles.length})
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                    {filteredFiles.map((file) => (
                      <Card
                        key={file.id}
                        className="p-4 cursor-pointer hover:bg-muted/50 transition-colors group"
                      >
                        <div className="flex items-start gap-3">
                          <div className="w-10 h-10 rounded-lg bg-muted flex items-center justify-center flex-shrink-0">
                            {getFileIcon(file.file_type)}
                          </div>
                          <div className="flex-1 min-w-0">
                            <h4 className="font-medium truncate text-sm">{file.filename}</h4>
                            <p className="text-xs text-muted-foreground mt-1">
                              {formatFileSize(file.file_size)} • {formatDate(file.updated_at)}
                            </p>
                          </div>
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button
                                variant="ghost"
                                size="icon"
                                className="opacity-0 group-hover:opacity-100 transition-opacity"
                                onClick={(e) => e.stopPropagation()}
                              >
                                <MoreVertical className="w-4 h-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem disabled>Скачать</DropdownMenuItem>
                              <DropdownMenuItem disabled>Переименовать</DropdownMenuItem>
                              <DropdownMenuItem disabled>Переместить</DropdownMenuItem>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem className="text-destructive" disabled>
                                Удалить
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </div>
                      </Card>
                    ))}
                  </div>
                </div>
              )}

              {/* Empty State */}
              {!loading && filteredFolders.length === 0 && filteredFiles.length === 0 && (
                <div className="flex flex-col items-center justify-center h-64 text-center">
                  <Folder className="w-16 h-16 text-muted-foreground mb-4" />
                  <h3 className="text-lg font-medium mb-2">Нет файлов или папок</h3>
                  <p className="text-muted-foreground mb-4">
                    {searchQuery ? "По вашему запросу ничего не найдено." : "Эта папка пуста."}
                  </p>
                </div>
              )}
            </div>
          ) : (
            // Hierarchy View
            <div className="space-y-2">
              <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-4">
                Иерархия файлов
              </h3>
              {buildHierarchyTree(currentFolderId)}
              {!loading && filteredFolders.length === 0 && filteredFiles.length === 0 && (
                <div className="flex flex-col items-center justify-center h-64 text-center">
                  <List className="w-16 h-16 text-muted-foreground mb-4" />
                  <h3 className="text-lg font-medium mb-2">Нет элементов для отображения</h3>
                  <p className="text-muted-foreground">
                    {searchQuery ? "По вашему запросу ничего не найдено." : "Эта папка пуста."}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
