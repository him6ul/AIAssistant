//
//  TaskViews.swift
//  AI Personal Assistant
//
//  Task management views
//

import SwiftUI

struct TaskViews: View {
    @ObservedObject var appState: AppState
    @State private var selectedView: TaskViewType = .today
    
    enum TaskViewType {
        case today
        case overdue
        case waitingOn
        case followUps
    }
    
    var body: some View {
        VStack(spacing: 0) {
            // Quick actions
            HStack(spacing: 8) {
                QuickActionButton(title: "Email Scan", action: appState.scanEmails)
                QuickActionButton(title: "OneNote Scan", action: appState.scanOneNote)
            }
            .padding()
            
            Divider()
            
            // View selector
            Picker("Task View", selection: $selectedView) {
                Text("Today").tag(TaskViewType.today)
                Text("Overdue").tag(TaskViewType.overdue)
                Text("Waiting On").tag(TaskViewType.waitingOn)
                Text("Follow-ups").tag(TaskViewType.followUps)
            }
            .pickerStyle(.segmented)
            .padding(.horizontal)
            
            // Task list
            if appState.isLoading {
                Spacer()
                ProgressView()
                Spacer()
            } else {
                TaskListView(appState: appState, viewType: selectedView)
            }
        }
    }
}

struct QuickActionButton: View {
    let title: String
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            Text(title)
                .font(.caption)
                .padding(.horizontal, 12)
                .padding(.vertical, 6)
                .background(Color.blue.opacity(0.1))
                .cornerRadius(8)
        }
        .buttonStyle(.plain)
    }
}

struct TaskListView: View {
    @ObservedObject var appState: AppState
    let viewType: TaskViews.TaskViewType
    
    private var filteredTasks: [Task] {
        switch viewType {
        case .today:
            return appState.tasks.filter { task in
                // Simplified - filter by due date
                task.status == "open"
            }
        case .overdue:
            return appState.tasks.filter { task in
                task.status == "open" && task.dueDate != nil
                // In production, compare with current date
            }
        case .waitingOn:
            return appState.tasks.filter { task in
                task.status == "open" && task.classification == "waiting-on"
            }
        case .followUps:
            return appState.tasks.filter { task in
                task.status == "open" && task.classification == "follow-up"
            }
        }
    }
    
    var body: some View {
        ScrollView {
            LazyVStack(alignment: .leading, spacing: 8) {
                if filteredTasks.isEmpty {
                    Text("No tasks found")
                        .foregroundColor(.secondary)
                        .padding()
                } else {
                    ForEach(filteredTasks) { task in
                        TaskRow(task: task)
                    }
                }
            }
            .padding()
        }
    }
}

struct TaskRow: View {
    let task: Task
    
    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text(task.title)
                    .font(.headline)
                Spacer()
                ImportanceBadge(importance: task.importance)
            }
            
            if let description = task.description, !description.isEmpty {
                Text(description)
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .lineLimit(2)
            }
            
            HStack {
                if let dueDate = task.dueDate {
                    Label(dueDate, systemImage: "calendar")
                        .font(.caption2)
                        .foregroundColor(.secondary)
                }
                
                Spacer()
                
                Text(task.classification.capitalized)
                    .font(.caption2)
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(Color.blue.opacity(0.1))
                    .cornerRadius(4)
            }
        }
        .padding()
        .background(Color(NSColor.controlBackgroundColor))
        .cornerRadius(8)
    }
}

struct ImportanceBadge: View {
    let importance: String
    
    var color: Color {
        switch importance.lowercased() {
        case "high":
            return .red
        case "medium":
            return .orange
        case "low":
            return .green
        default:
            return .gray
        }
    }
    
    var body: some View {
        Circle()
            .fill(color)
            .frame(width: 8, height: 8)
    }
}

// Task model for SwiftUI
struct Task: Identifiable, Codable {
    let id: Int
    let title: String
    let description: String?
    let dueDate: String?
    let peopleInvolved: [String]
    let source: String
    let importance: String
    let classification: String
    let status: String
    
    enum CodingKeys: String, CodingKey {
        case id
        case title
        case description
        case dueDate = "due_date"
        case peopleInvolved = "people_involved"
        case source
        case importance
        case classification
        case status
    }
}

