//
//  MenuBarApp.swift
//  AI Personal Assistant
//
//  Main menu bar application entry point
//

import SwiftUI
import AppKit

@main
struct MenuBarApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) var appDelegate
    
    var body: some Scene {
        Settings {
            EmptyView()
        }
    }
}

class AppDelegate: NSObject, NSApplicationDelegate {
    var statusBarItem: NSStatusItem?
    var popover: NSPopover?
    
    func applicationDidFinishLaunching(_ notification: Notification) {
        // Create status bar item
        statusBarItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
        
        if let button = statusBarItem?.button {
            button.image = NSImage(systemSymbolName: "brain.head.profile", accessibilityDescription: "AI Assistant")
            button.action = #selector(togglePopover)
            button.target = self
        }
        
        // Create popover
        popover = NSPopover()
        popover?.contentSize = NSSize(width: 400, height: 600)
        popover?.behavior = .transient
        popover?.contentViewController = NSHostingController(rootView: MainView())
    }
    
    @objc func togglePopover() {
        if let button = statusBarItem?.button {
            if let popover = popover {
                if popover.isShown {
                    popover.performClose(nil)
                } else {
                    popover.show(relativeTo: button.bounds, of: button, preferredEdge: .minY)
                }
            }
        }
    }
}

class AppState: ObservableObject {
    static let shared = AppState()
    
    @Published var isOnline: Bool = false
    @Published var llmMode: String = "Unknown"
    @Published var tasks: [Task] = []
    @Published var isLoading: Bool = false
    
    private let apiClient = APIClient()
    
    private init() {
        checkStatus()
        loadTasks()
    }
    
    func checkStatus() {
        apiClient.getStatus { [weak self] status in
            DispatchQueue.main.async {
                self?.isOnline = status?.network == "online"
                self?.llmMode = status?.llmMode ?? "Unknown"
            }
        }
    }
    
    func loadTasks() {
        isLoading = true
        apiClient.getTasks { [weak self] tasks in
            DispatchQueue.main.async {
                self?.tasks = tasks ?? []
                self?.isLoading = false
            }
        }
    }
    
    func scanEmails() {
        isLoading = true
        apiClient.scanEmails { [weak self] result in
            DispatchQueue.main.async {
                self?.isLoading = false
                if result != nil {
                    self?.loadTasks()
                }
            }
        }
    }
    
    func scanOneNote() {
        isLoading = true
        apiClient.scanOneNote { [weak self] result in
            DispatchQueue.main.async {
                self?.isLoading = false
                if result != nil {
                    self?.loadTasks()
                }
            }
        }
    }
}

struct MainView: View {
    @StateObject private var appState = AppState.shared
    @State private var selectedTab: Tab = .chat
    
    enum Tab {
        case chat
        case tasks
    }
    
    var body: some View {
        VStack(spacing: 0) {
            // Header
            HStack {
                Text("AI Assistant")
                    .font(.headline)
                Spacer()
                StatusIndicator(isOnline: appState.isOnline, mode: appState.llmMode)
            }
            .padding()
            .background(Color(NSColor.controlBackgroundColor))
            
            Divider()
            
            // Tab selector
            Picker("View", selection: $selectedTab) {
                Text("Chat").tag(Tab.chat)
                Text("Tasks").tag(Tab.tasks)
            }
            .pickerStyle(.segmented)
            .padding()
            
            // Content
            if selectedTab == .chat {
                ChatView()
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                TaskViews(appState: appState)
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            }
        }
        .frame(width: 400, height: 600)
    }
}

struct StatusIndicator: View {
    let isOnline: Bool
    let mode: String
    
    var body: some View {
        HStack(spacing: 4) {
            Circle()
                .fill(isOnline ? Color.green : Color.orange)
                .frame(width: 8, height: 8)
            Text(mode)
                .font(.caption)
                .foregroundColor(.secondary)
        }
    }
}

