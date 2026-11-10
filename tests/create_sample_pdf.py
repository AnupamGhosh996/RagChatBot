"""
Generates a multi-page sample PDF for testing the PDF Intelligence RAG pipeline.
Does not require any 3rd-party dependencies (generates raw PDF 1.4 objects).
"""
import os
from pathlib import Path

def create_sample_pdf(output_path: str = "sample_os_notes.pdf") -> str:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # We write a clean 3-page PDF with clear factual content
    # Page 1: Operating Systems & Kernel Architecture
    # Page 2: Memory Management and Virtual Memory
    # Page 3: CPU Scheduling and Deadlock Prevention
    
    pages_content = [
        # Page 1
        "PDF Intelligence Test Document: Operating Systems Architecture\n"
        "Document: OS_Notes.pdf - Page 1\n\n"
        "1. Introduction to Operating Systems\n"
        "An Operating System (OS) is system software that acts as an intermediary between computer hardware and the computer user. "
        "The primary purpose of an operating system is to provide an environment in which a user can execute programs in a convenient and efficient manner. "
        "The operating system manages hardware resources and provides services to application programs.\n\n"
        "2. Kernel Architecture\n"
        "The kernel is the core component of the operating system. It remains loaded in main memory at all times. "
        "A monolithic kernel executes all operating system services in the supervisor address space, providing high execution speed. "
        "In contrast, a microkernel structure minimizes the kernel by moving non-essential components into user space, "
        "which improves system modularity, fault tolerance, and security.",

        # Page 2
        "PDF Intelligence Test Document: Memory Management\n"
        "Document: OS_Notes.pdf - Page 2\n\n"
        "3. Memory Hierarchy and Allocation\n"
        "Main memory is central to the operation of a modern computer system. It consists of a large array of bytes, each with its own physical address. "
        "Contiguous memory allocation assigns consecutive blocks of memory to processes, which frequently causes external fragmentation.\n\n"
        "4. Virtual Memory and Paging\n"
        "Virtual memory separates logical memory as perceived by programmers from physical memory. "
        "Paging avoids external fragmentation by dividing physical memory into fixed-sized blocks called frames, "
        "and logical memory into blocks of the exact same size called pages. "
        "The Translation Lookaside Buffer (TLB) is a high-speed associative hardware cache used to accelerate virtual address translation. "
        "When a referenced page is not present in physical RAM, a page fault occurs, prompting the OS to fetch the page from secondary storage.",

        # Page 3
        "PDF Intelligence Test Document: CPU Scheduling & Concurrency\n"
        "Document: OS_Notes.pdf - Page 3\n\n"
        "5. CPU Scheduling Algorithms\n"
        "CPU scheduling is the basis of multi-programmed operating systems. By switching the CPU among processes, the operating system makes the computer more productive. "
        "Common algorithms include First-Come First-Served (FCFS), Shortest Job First (SJF), Priority Scheduling, and Round Robin (RR). "
        "Round Robin scheduling uses a fixed time slice or quantum, providing fair response time for interactive time-sharing systems.\n\n"
        "6. Deadlock Conditions\n"
        "A deadlock occurs when a set of processes are blocked because each process is holding a resource and waiting for another resource held by another process. "
        "Coffman identified four necessary conditions for deadlock:\n"
        "1. Mutual Exclusion: At least one resource must be held in a non-shareable mode.\n"
        "2. Hold and Wait: A process must be holding at least one resource and waiting to acquire additional resources.\n"
        "3. No Preemption: Resources cannot be preempted forcibly from a process.\n"
        "4. Circular Wait: A closed chain of processes exists such that each process holds resources needed by the next process."
    ]

    # Generate PDF Objects
    # Object 1: Catalog
    # Object 2: Pages
    # Object 3, 5, 7: Page objects
    # Object 4, 6, 8: Content streams
    # Object 9: Font

    def escape_pdf_text(txt):
        return txt.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')

    objects = []
    
    # 1: Catalog
    objects.append("1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
    
    # 2: Pages
    page_refs = "3 0 R 5 0 R 7 0 R"
    objects.append(f"2 0 obj\n<< /Type /Pages /Kids [{page_refs}] /Count 3 >>\nendobj\n")

    # Font object (will be object 9)
    font_ref = "9 0 R"

    for i, content in enumerate(pages_content):
        page_obj_id = 3 + i * 2
        stream_obj_id = 4 + i * 2

        # Format stream with text layout
        stream_lines = ["BT", "/F1 11 Tf", "40 750 Td", "16 TL"]
        for paragraph in content.split("\n"):
            if not paragraph.strip():
                stream_lines.append("T*")
                continue
            # Wrap lines simply at 80 chars
            words = paragraph.split(" ")
            line = ""
            for w in words:
                if len(line) + len(w) + 1 > 75:
                    stream_lines.append(f"({escape_pdf_text(line)}) Tj")
                    stream_lines.append("T*")
                    line = w
                else:
                    line = f"{line} {w}".strip()
            if line:
                stream_lines.append(f"({escape_pdf_text(line)}) Tj")
                stream_lines.append("T*")

        stream_lines.append("ET")
        stream_data = "\n".join(stream_lines)

        # Page Object
        objects.append(
            f"{page_obj_id} 0 obj\n"
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents {stream_obj_id} 0 R /Resources << /Font << /F1 {font_ref} >> >> >>\n"
            f"endobj\n"
        )

        # Stream Object
        objects.append(
            f"{stream_obj_id} 0 obj\n"
            f"<< /Length {len(stream_data.encode('latin1'))} >>\n"
            f"stream\n{stream_data}\nendstream\nendobj\n"
        )

    # 9: Font Object
    objects.append(
        "9 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
    )

    # Assemble file with xref
    header = "%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
    offsets = []
    current_offset = len(header.encode("latin1"))

    body = ""
    for obj in objects:
        offsets.append(current_offset)
        obj_bytes = obj.encode("latin1")
        current_offset += len(obj_bytes)
        body += obj

    xref_offset = current_offset
    xref = f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n"
    for offset in offsets:
        xref += f"{offset:010d} 00000 n \n"

    trailer = (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n"
    )

    pdf_content = header + body + xref + trailer

    with open(path, "wb") as f:
        f.write(pdf_content.encode("latin1"))

    print(f"Sample PDF successfully generated at: {path.resolve()}")
    return str(path.resolve())

if __name__ == "__main__":
    create_sample_pdf()
