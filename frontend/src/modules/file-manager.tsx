"use client"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import { Search, Home, FolderPlus, Upload, List, Download, Info, CheckCircle2, Folder, ChevronRight, ArrowLeft, File, MoreVertical, Move, Edit, Trash2 } from 'lucide-react'
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

type FolderItem = {
  id: string
  name: string
  createdAt: Date
  parentId: string | null
}

type FileItem = {
  id: string
  name: string
  size: number
  createdAt: Date
  parentId: string | null
}

export function FileManager() {
  const [searchQuery, setSearchQuery] = useState("")
  const [currentPath, setCurrentPath] = useState<Array<{ id: string; name: string }>>([
    { id: "root", name: "home" },
    { id: "user", name: "user" },
  ])
  const [currentFolderId, setCurrentFolderId] = useState<string | null>(null)

  const [folders, setFolders] = useState<FolderItem[]>([
    { id: "1", name: "Documents", createdAt: new Date("2025-10-18"), parentId: null },
    { id: "2", name: "Projects", createdAt: new Date("2025-10-17"), parentId: null },
    { id: "3", name: "fg", createdAt: new Date("2025-10-16"), parentId: null },
    { id: "4", name: "dima", createdAt: new Date("2025-10-16"), parentId: null },
    { id: "5", name: "МарияМария", createdAt: new Date("2025-10-16"), parentId: null },
  ])

  const [files, setFiles] = useState<FileItem[]>([
    { id: "f1", name: "Book1qwre3.xlsx", size: 206.95, createdAt: new Date("2025-10-23"), parentId: null },
    { id: "f2", name: "sample.xlsx", size: 7.83, createdAt: new Date("2025-10-21"), parentId: null },
    { id: "f3", name: "c2fe42b9-a6db-415....xlsx", size: 87.82, createdAt: new Date("2025-10-21"), parentId: null },
  ])

  const [editingFolderId, setEditingFolderId] = useState<string | null>(null)
  const [editingName, setEditingName] = useState("")
  const inputRef = useRef<HTMLInputElement>(null)

  const [moveMode, setMoveMode] = useState<{ active: boolean; fileId: string | null }>({
    active: false,
    fileId: null,
  })
  const [selectedDestinationFolder, setSelectedDestinationFolder] = useState<string | null>(null)
  const [contextMenu, setContextMenu] = useState<{ fileId: string; x: number; y: number } | null>(null)

  const visibleFolders = folders.filter((folder) => folder.parentId === currentFolderId)
  const visibleFiles = files.filter((file) => file.parentId === currentFolderId)

  useEffect(() => {
    const handleClickOutside = () => setContextMenu(null)
    if (contextMenu) {
      document.addEventListener("click", handleClickOutside)
      return () => document.removeEventListener("click", handleClickOutside)
    }
  }, [contextMenu])

  useEffect(() => {
    if (editingFolderId && inputRef.current) {
      inputRef.current.focus()
      inputRef.current.select()
    }
  }, [editingFolderId])

  const handleCreateFolder = () => {
    const newFolder: FolderItem = {
      id: Date.now().toString(),
      name: "New folder",
      createdAt: new Date(),
      parentId: currentFolderId,
    }
    setFolders([...folders, newFolder])
    setEditingFolderId(newFolder.id)
    setEditingName(newFolder.name)
  }

  const handleSaveFolderName = () => {
    if (editingFolderId && editingName.trim()) {
      setFolders(
        folders.map((folder) => (folder.id === editingFolderId ? { ...folder, name: editingName.trim() } : folder)),
      )
    } else if (editingFolderId && !editingName.trim()) {
      setFolders(folders.filter((folder) => folder.id !== editingFolderId))
    }
    setEditingFolderId(null)
    setEditingName("")
  }

  const handleCancelEdit = () => {
    if (editingFolderId) {
      const folder = folders.find((f) => f.id === editingFolderId)
      if (folder && folder.name === "New folder" && editingName === "New folder") {
        setFolders(folders.filter((f) => f.id !== editingFolderId))
      }
    }
    setEditingFolderId(null)
    setEditingName("")
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleSaveFolderName()
    } else if (e.key === "Escape") {
      handleCancelEdit()
    }
  }

  const handleFolderDoubleClick = (folder: FolderItem) => {
    if (editingFolderId === folder.id) return
    setCurrentFolderId(folder.id)
    setCurrentPath([...currentPath, { id: folder.id, name: folder.name }])
  }

  const handlePathClick = (index: number) => {
    const newPath = currentPath.slice(0, index + 1)
    setCurrentPath(newPath)
    setCurrentFolderId(index < 2 ? null : newPath[newPath.length - 1].id)
  }

  const handleGoBack = () => {
    if (currentPath.length > 2) {
      const newPath = currentPath.slice(0, -1)
      setCurrentPath(newPath)
      setCurrentFolderId(newPath[newPath.length - 1].id)
    } else {
      setCurrentPath([
        { id: "root", name: "home" },
        { id: "user", name: "user" },
      ])
      setCurrentFolderId(null)
    }
  }

  const handleMoveFile = (fileId: string) => {
    setMoveMode({ active: true, fileId })
    setContextMenu(null)
  }

  const handleSelectDestination = (folderId: string) => {
    setSelectedDestinationFolder(folderId)
  }

  const handleConfirmMove = () => {
    if (moveMode.fileId && selectedDestinationFolder) {
      setFiles(
        files.map((file) => (file.id === moveMode.fileId ? { ...file, parentId: selectedDestinationFolder } : file)),
      )
    }
    setMoveMode({ active: false, fileId: null })
    setSelectedDestinationFolder(null)
  }

  const handleCancelMove = () => {
    setMoveMode({ active: false, fileId: null })
    setSelectedDestinationFolder(null)
  }

  const handleFileContextMenu = (e: React.MouseEvent, fileId: string) => {
    e.preventDefault()
    setContextMenu({ fileId, x: e.clientX, y: e.clientY })
  }

  return (
    <div className="flex h-screen bg-white text-foreground">
      {/* Sidebar */}
      <aside className="w-64 border-r border-gray-200 bg-white flex flex-col">
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gray-900 flex items-center justify-center">
              <Folder className="w-5 h-5 text-white" />
            </div>
          </div>
        </div>

        <nav className="flex-1 p-4 space-y-2">
          <Button
            variant="ghost"
            className="w-full justify-start gap-3 text-gray-900 hover:bg-gray-100 font-medium"
            onClick={() => {
              setCurrentPath([
                { id: "root", name: "home" },
                { id: "user", name: "user" },
              ])
              setCurrentFolderId(null)
            }}
          >
            <Home className="w-5 h-5" />
            My files
          </Button>
          <Button
            variant="ghost"
            className="w-full justify-start gap-3 text-gray-600 hover:bg-gray-100 hover:text-gray-900"
            onClick={handleCreateFolder}
          >
            <FolderPlus className="w-5 h-5" />
            New folder
          </Button>
          <Button
            variant="ghost"
            className="w-full justify-start gap-3 text-gray-600 hover:bg-gray-100 hover:text-gray-900"
          >
            <Upload className="w-5 h-5" />
            Upload file
          </Button>
        </nav>

        <div className="p-4 border-t border-gray-200 text-xs text-gray-500">
          File Browser v1.9.0
          <div className="mt-1">Help</div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col">
        {/* Header */}
        <header className="border-b border-gray-200 bg-white p-4">
          <div className="flex items-center gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <Input
                type="text"
                placeholder="Search or execute a command..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 bg-white border-gray-200 text-gray-900 placeholder:text-gray-400 focus-visible:ring-gray-300"
              />
            </div>
            <div className="flex items-center gap-2">
              {moveMode.active ? (
                <>
                  <Button
                    onClick={handleConfirmMove}
                    disabled={!selectedDestinationFolder}
                    className="bg-gray-900 text-white hover:bg-gray-800 disabled:opacity-50"
                  >
                    <CheckCircle2 className="w-4 h-4 mr-2" />
                    Confirm Move
                  </Button>
                  <Button
                    onClick={handleCancelMove}
                    variant="outline"
                    className="border-gray-200 text-gray-900 hover:bg-gray-100"
                  >
                    Cancel
                  </Button>
                </>
              ) : (
                <>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="text-gray-500 hover:text-gray-900 hover:bg-gray-100"
                  >
                    <List className="w-5 h-5" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="text-gray-500 hover:text-gray-900 hover:bg-gray-100"
                  >
                    <Download className="w-5 h-5" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="text-gray-500 hover:text-gray-900 hover:bg-gray-100"
                  >
                    <Upload className="w-5 h-5" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="text-gray-500 hover:text-gray-900 hover:bg-gray-100"
                  >
                    <Info className="w-5 h-5" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="text-gray-500 hover:text-gray-900 hover:bg-gray-100"
                  >
                    <CheckCircle2 className="w-5 h-5" />
                  </Button>
                </>
              )}
            </div>
          </div>
        </header>

        <div className="border-b border-gray-200 bg-white px-8 py-3">
          <div className="flex items-center gap-3 text-sm">
            <button
              onClick={handleGoBack}
              className="text-gray-500 hover:text-gray-900 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={currentPath.length <= 2}
            >
              <ArrowLeft className="w-4 h-4" />
            </button>
            <button
              onClick={() => handlePathClick(-1)}
              className="text-gray-900 hover:text-gray-700 transition-colors font-medium"
            >
              /
            </button>
            {currentPath.map((segment, index) => (
              <div key={segment.id} className="flex items-center gap-2">
                <ChevronRight className="w-4 h-4 text-gray-400" />
                <button
                  onClick={() => handlePathClick(index)}
                  className={
                    index === currentPath.length - 1
                      ? "text-gray-900 font-semibold"
                      : "text-gray-600 hover:text-gray-900 transition-colors"
                  }
                >
                  {segment.name}
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-auto p-8 bg-white">
          {visibleFolders.length === 0 && visibleFiles.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <div className="w-24 h-24 rounded-full bg-gray-50 border-2 border-gray-200 flex items-center justify-center mx-auto mb-6">
                  <Folder className="w-12 h-12 text-gray-400" />
                </div>
                <h2 className="text-xl font-semibold text-gray-900 mb-2">No folders or files</h2>
                <p className="text-gray-500 mb-6">
                  This directory is empty. Upload a file or create a new folder to get started.
                </p>
                <div className="flex items-center justify-center gap-3">
                  <Button className="bg-gray-900 text-white hover:bg-gray-800">
                    <Upload className="w-4 h-4 mr-2" />
                    Upload file
                  </Button>
                  <Button
                    variant="outline"
                    className="border-gray-300 text-gray-900 hover:bg-gray-50"
                    onClick={handleCreateFolder}
                  >
                    <FolderPlus className="w-4 h-4 mr-2" />
                    New folder
                  </Button>
                </div>
              </div>
            </div>
          ) : (
            <div className="space-y-8">
              {moveMode.active && (
                <div className="bg-gray-50 border border-gray-300 rounded-lg p-4 text-center">
                  <p className="text-gray-900 font-medium">Select a destination folder and click "Confirm Move"</p>
                </div>
              )}

              {/* Folders Section */}
              {visibleFolders.length > 0 && (
                <div>
                  <h3 className="text-xs font-semibold text-gray-500 mb-4 uppercase tracking-wider">
                    Folders ({visibleFolders.length})
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                    {visibleFolders.map((folder) => (
                      <div
                        key={folder.id}
                        className={`bg-white border rounded-lg p-4 transition-all cursor-pointer hover:shadow-md ${
                          moveMode.active && selectedDestinationFolder === folder.id
                            ? "border-gray-900 border-2 shadow-md"
                            : "border-gray-200 hover:border-gray-300"
                        }`}
                        onDoubleClick={() => !moveMode.active && handleFolderDoubleClick(folder)}
                        onClick={() => moveMode.active && handleSelectDestination(folder.id)}
                      >
                        <div className="flex items-start gap-3">
                          <Folder className="w-8 h-8 text-gray-700 flex-shrink-0 mt-0.5" />
                          <div className="flex-1 min-w-0">
                            {editingFolderId === folder.id ? (
                              <input
                                ref={inputRef}
                                type="text"
                                value={editingName}
                                onChange={(e) => setEditingName(e.target.value)}
                                onBlur={handleSaveFolderName}
                                onKeyDown={handleKeyDown}
                                className="w-full bg-transparent text-gray-900 border-0 border-b border-gray-900 px-1 py-0.5 font-sans font-medium text-sm focus:outline-none focus:border-gray-900"
                              />
                            ) : (
                              <div
                                className="text-gray-900 font-sans font-medium text-sm truncate cursor-pointer"
                                onClick={(e) => {
                                  if (!moveMode.active) {
                                    e.stopPropagation()
                                    setEditingFolderId(folder.id)
                                    setEditingName(folder.name)
                                  }
                                }}
                              >
                                {folder.name}
                              </div>
                            )}
                            <div className="text-[11px] text-gray-500 mt-1">
                              {folder.createdAt.toLocaleDateString("en-GB")}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {visibleFiles.length > 0 && (
                <div>
                  <h3 className="text-xs font-semibold text-gray-500 mb-4 uppercase tracking-wider">
                    Files ({visibleFiles.length})
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                    {visibleFiles.map((file) => (
                      <div
                        key={file.id}
                        className="bg-white border border-gray-200 rounded-lg p-4 hover:border-gray-300 hover:shadow-md transition-all cursor-pointer relative group"
                        onContextMenu={(e) => handleFileContextMenu(e, file.id)}
                      >
                        <div className="flex items-start gap-3">
                          <File className="w-8 h-8 text-gray-600 flex-shrink-0 mt-0.5" />
                          <div className="flex-1 min-w-0">
                            <div className="text-gray-900 font-sans font-medium text-sm truncate">
                              {file.name}
                            </div>
                            <div className="text-[11px] text-gray-500 mt-1">
                              {file.size} KB • {file.createdAt.toLocaleDateString("en-GB")}
                            </div>
                          </div>
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              handleFileContextMenu(e as any, file.id)
                            }}
                            className="opacity-0 group-hover:opacity-100 transition-opacity"
                          >
                            <MoreVertical className="w-4 h-4 text-gray-500 hover:text-gray-900" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </main>

      {contextMenu && (
        <div
          className="fixed bg-white border border-gray-300 rounded-lg shadow-lg py-2 z-50 min-w-[200px]"
          style={{ left: contextMenu.x, top: contextMenu.y }}
          onClick={(e) => e.stopPropagation()}
        >
          <button
            onClick={() => handleMoveFile(contextMenu.fileId)}
            className="w-full px-4 py-2.5 text-left text-gray-900 hover:bg-gray-100 flex items-center gap-3 text-sm transition-colors"
          >
            <Move className="w-4 h-4" />
            Move
          </button>
          <button className="w-full px-4 py-2.5 text-left text-gray-900 hover:bg-gray-100 flex items-center gap-3 text-sm transition-colors">
            <Download className="w-4 h-4" />
            Download
            <span className="ml-auto text-gray-500 text-xs">Ctrl+D</span>
          </button>
          <button className="w-full px-4 py-2.5 text-left text-gray-900 hover:bg-gray-100 flex items-center gap-3 text-sm transition-colors">
            <Edit className="w-4 h-4" />
            Rename
          </button>
          <div className="border-t border-gray-200 my-1" />
          <button className="w-full px-4 py-2.5 text-left text-red-600 hover:bg-red-50 flex items-center gap-3 text-sm transition-colors">
            <Trash2 className="w-4 h-4" />
            Delete
          </button>
        </div>
      )}
    </div>
  )
}
